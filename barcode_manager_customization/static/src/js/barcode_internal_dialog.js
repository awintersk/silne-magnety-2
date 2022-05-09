odoo.define('barcode_manager_customization.BarcodeInternalDialog', function (require) {
    'use strict'

    const {SecondaryBody, RECORD_ID_CODE, useWatchDog} = require('barcode_manager_customization.secondary_body')
    const Dialog = require('web.OwlDialog')
    const {useState} = owl

    /**
     * @typedef {{
     *   packageItems: {
     *      id: Number,
     *      name: String,
     *      packaging_id: Array<Number|String>,
     *      shipping_weight: Number,
     *      weight: Number,
     *   }[]|[],
     *   packageTypeItems: {id: Number, name: String, packing_type: String}[]|[],
     *   boxIntId: Number,
     *   packageTypeIntId: Number,
     *   qty: Number,
     *   shipping_weight: Number,
     *   weight: Number,
     * }} BarcodeInternalDialogState
     */

    /**
     * @typedef {{id: Number, name: String, [result_package_id]: Array<Number|String> | undefined}} ILineRecord
     */

    /**
     * @param {Number} value
     * @param {Number} [precision]
     * @returns {Number}
     */
    function round(value, precision) {
        if (precision === undefined) {
            precision = 1000
        } else {
            precision = Math.pow(10, precision)
        }
        return Math.round(value * precision) / precision
    }

    /**
     * @extends SecondaryBody
     * @property {{
     *     moveLineIds: Object[],
     *     linesId: Object,
     *     pickingIntId: Number,
     * }} props
     */
    class BarcodeInternalDialog extends SecondaryBody {
        setup() {
            /**@type{BarcodeInternalDialogState}*/
            this.state = useState({
                packageItems: [],
                packageTypeItems: [],
                boxIntId: this.initialResultPackageID,
                packageTypeIntId: 0,
                qty: this.props.linesId.product_uom_qty || 0,
                shipping_weight: 0,
                weight: 0,
                isMoved: false,
            })

            this.eventSetup()

            useWatchDog({
                state: this.state,
                field: 'boxIntId',
                callback: this._onChangePackage,
            })
            useWatchDog({
                state: this.state,
                field: 'qty',
                callback: this._onChangeQty,
            })
            useWatchDog({
                state: this.state,
                field: 'packageTypeIntId',
                callback: this._onChangePackageTypeIntId,
            })
        }

        async willStart() {
            await this.fetchPackage()

            const [relatedSaleId] = await this.rpc({
                model: 'sale.order',
                method: 'search_read',
                domain: [['picking_ids', 'in', this.props.pickingIntId]],
                fields: ['name'],
                limit: 1
            })

            this.state.packageItems = await this.rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [
                    ['sale_ids', 'in', [relatedSaleId.id]],
                    ['packaging_id', 'in', this.state.packageTypeItems.map(el => el.id)]
                ],
                fields: ['name', 'packaging_id', 'shipping_weight', 'weight'],
                orderBy: [{name: 'id', asc: false}]
            })

            if (!this.state.boxIntId) {
                this.state.boxIntId = this.defaultResultPackageIntId
            }

            if (this.state.boxIntId > 0) {
                const packageId = this.state.packageItems.find(el => el.id === this.state.boxIntId)
                Object.assign(this.state, {
                    shipping_weight: packageId ? packageId.shipping_weight : 0,
                    weight: packageId ? this._computeExpectedWeight(packageId) : 0,
                    packageTypeIntId: packageId && packageId.packaging_id ? packageId.packaging_id[0] : 0,
                })
            }
        }

        mounted() {
            this.parentWidget.trigger('default-barcode-scanner', {active: false})
        }

        get notification() {
            return this.env.services.notification
        }

        get parentWidget() {
            return this.__owl__.parent.parentWidget
        }

        /**
         * @return {Number}
         */
        get defaultResultPackageIntId() {
            const {linesId, packageList} = this.props
            const [resultPackageID] = linesId.result_package_id || []
            const [packageID] = linesId.package_id || []

            if (!resultPackageID && !packageID) {
                return packageList.length ? packageList[0] : RECORD_ID_CODE.NEW
            }

            return resultPackageID || packageID || RECORD_ID_CODE.NEW
        }

        /**
         * @returns {Number}
         */
        get productWeight() {
            return this.props.linesId.product_weight
        }

        /**
         * @returns {Number}
         */
        get initialResultPackageID() {
            const resultPackage = this.props.linesId.result_package_id
            if (_.isEmpty(resultPackage)) {
                return 0
            }
            return resultPackage[0]
        }

        /**
         * @param {String} barcode
         * @returns {Promise<void>}
         * @private
         */
        async _onBarcodeScanned(barcode) {
            const [packageId] = await this.rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [['name', '=', barcode]],
                fields: ['id', 'name', 'packaging_id']
            })
            if (packageId) {
                const packageTypeIntId = packageId.packaging_id ? packageId.packaging_id[0] : 0

                if (!this.state.packageItems.find(el => el.id === packageId.id)) {
                    this.state.packageItems.unshift(packageId)
                }

                this.state.boxIntId = packageId.id
                this.state.packageTypeIntId = packageTypeIntId
            } else {
                this.state.boxIntId = RECORD_ID_CODE.NONE
                this.state.packageTypeIntId = 0
                this.env.services.notification.notify({
                    type: 'danger',
                    title: 'Barcode',
                    message: `Package with barcode: <strong>${barcode}</strong> is not found!`
                })
            }

        }

        get _isValidData() {
            return this.state.qty <= this.props.linesId.product_uom_qty
        }

        onClose() {
            this.trigger('reload')
            this.destroy()
        }

        async moveToPackage() {
            const newPackage = await this.rpc({
                model: 'stock.move.line',
                method: 'split_and_put_in_pack',
                args: [this.props.linesId.id],
                kwargs: {
                    qty: this.state.qty,
                    package_int_id: +this.state.boxIntId,
                    package_type_int_id: +this.state.packageTypeIntId,
                    weight: this.state.shipping_weight,
                    is_new_package: Boolean(+this.state.boxIntId === 0)
                },
                context: {
                    picking_id: this.props.pickingIntId
                },
            })

            if (newPackage) {
                this.state.packageItems.unshift(newPackage)
                this.state.boxIntId = newPackage.id
            }

            this.notification.notify({
                type: 'info',
                title: this.props.linesId.display_name || '',
                message: 'Successfully moved.'
            })
            this.state.isMoved = true
        }

        async _onPrint() {
            this.parentWidget.do_action('zpl_label_template.action_box_report', {
                    additional_context: {
                        active_ids: [Number(this.state.boxIntId)]
                    }
                }
            )
        }

        _onChangePackage() {
            const boxId = Number(this.state.boxIntId)
            const {state} = this

            /**@type{{packaging_id: Array<Number | String>, weight: Number}}*/
            const item = state.packageItems.find(el => el.id === boxId)

            if (boxId > 0 && item && item.packaging_id) {
                state.packageTypeIntId = item.packaging_id[0]
            } else {
                state.packageTypeIntId = 0
            }

            state.weight = this._computeExpectedWeight(item && item.id ? item : {})
        }

        _onChangeQty() {
            const {state} = this
            const packageId = state.packageItems.find(el => el.id === +state.boxIntId)
            state.weight = this._computeExpectedWeight(packageId ? packageId : {})
        }

        /**
         * @param {Number} [weight]
         * @returns {Number}
         * @private
         */
        _computeExpectedWeight({weight}) {
            const {
                packageTypeItems,
                packageTypeIntId,
                boxIntId,
                qty
            } = this.state

            if (weight === undefined) {
                const packagingId = packageTypeItems.find(el => el.id === +packageTypeIntId)
                weight = packagingId && packagingId.id ? packagingId.weight : 0
            }

            for (let lineId of this.props.moveLineIds) {
                const {product_weight} = lineId
                if (lineId.id === this.props.linesId.id) continue;
                if (lineId.result_package_id[0] === Number(boxIntId) && product_weight) {
                    weight += product_weight * lineId.qty_done
                }
            }

            return round(weight + this.productWeight * qty, 4)
        }

        _onChangePackageTypeIntId() {
            const {state} = this
            const packageId = state.packageItems.find(el => el.id === +state.boxIntId)
            state.weight = this._computeExpectedWeight(packageId && packageId.id ? packageId : {})
        }

        willUnmount() {
            this.parentWidget.trigger('default-barcode-scanner', {active: true})
        }
    }

    Object.assign(BarcodeInternalDialog, {
        template: 'barcode_manager_customization.receipt_internal_body',
        components: {Dialog},
        props: {
            moveLineIds: {
                type: Array,
                element: Object,
            },
            linesId: Object,
            pickingIntId: Number,
            packageList: {
                type: Array,
                element: Number
            }
        },
    })

    return {BarcodeInternalDialog, round}
});