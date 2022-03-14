odoo.define('barcode_manager_customization.BarcodeInternalDialog', function (require) {
    'use strict'

    const {SecondaryBody, RECORD_ID_CODE, useWatchDog} = require('barcode_manager_customization.secondary_body')
    const Dialog = require('web.OwlDialog')
    const {useState} = owl

    /**
     * @typedef {{
     *   packageItems: {id: Number, name: String, packaging_id: Array<Number|String>, shipping_weight: Number}[]|[],
     *   packageTypeItems: {id: Number, name: String, packing_type: String}[]|[],
     *   boxIntId: Number,
     *   packageTypeIntId: Number,
     *   qty: Number,
     *   shipping_weight: Number,
     * }} BarcodeInternalDialogState
     */

    /**
     * @typedef {{id: Number, name: String, [result_package_id]: Array<Number|String> | undefined}} ILineRecord
     */

    /**
     * @extends SecondaryBody
     */
    class BarcodeInternalDialog extends SecondaryBody {
        setup() {
            /**@type{BarcodeInternalDialogState}*/
            this.state = useState({
                packageItems: [],
                packageTypeItems: [],
                boxIntId: 0,
                packageTypeIntId: 0,
                qty: this.props.linesId.product_uom_qty || 0,
                shipping_weight: 0,
                isMoved: false,
            })
            this.eventSetup()
            useWatchDog({
                state: this.state,
                field: 'boxIntId',
                callback: this._onChangePackage,
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
                    ['name', 'ilike', `${relatedSaleId.name}-%%`],
                    ['packaging_id', 'in', this.state.packageTypeItems.map(el => el.id)]
                ],
                fields: ['name', 'packaging_id', 'shipping_weight'],
                orderBy: [{name: 'id', asc: false}]
            })

            this.state.boxIntId = this.defaultResultPackageIntId

            if (this.state.boxIntId > 0) {
                const packageId = this.state.packageItems.find(el => el.id === this.state.boxIntId)
                this.state.shipping_weight = packageId ? packageId.shipping_weight : 0
                this.state.packageTypeIntId = packageId && packageId.packaging_id ? packageId.packaging_id[0] : 0
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
            const {result_package_id, package_id} = this.props.linesId
            const itemsIntIds = this.state.packageItems.map(el => el.id)

            if (!itemsIntIds.includes(package_id[0])) {
                return RECORD_ID_CODE.NEW
            }

            if (!itemsIntIds.includes(result_package_id[0])) {
                return RECORD_ID_CODE.NEW
            }

            if (result_package_id) {
                return result_package_id[0] || RECORD_ID_CODE.NEW
            } else if (package_id) {
                return package_id[0] || RECORD_ID_CODE.NEW
            }
            return RECORD_ID_CODE.NEW
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

        async savePackageWeight() {
            if (this.state.boxIntId <= 0) return Promise.reject()
            if (typeof this.state.shipping_weight !== 'number') return Promise.reject()

            await this.rpc({
                model: 'stock.quant.package',
                method: 'write',
                args: [[this.state.boxIntId], {
                    'shipping_weight': this.state.shipping_weight
                }]
            })

            this.notification.notify({
                type: 'info',
                title: 'Package',
                message: `<b>Weight</b>: ${this.state.shipping_weight}kg`
            })
        }

        async _onPrint() {
            this.parentWidget.do_action('zpl_label_template.action_box_report', {
                    additional_context: {
                        active_ids: [Number(this.state.boxIntId)]
                    }
                }
            )
        }

        willUnmount() {
            this.parentWidget.trigger('default-barcode-scanner', {active: true})
        }
    }

    Object.assign(BarcodeInternalDialog, {
        template: 'barcode_manager_customization.receipt_internal_body',
        components: {Dialog}
    })

    return {BarcodeInternalDialog}
});