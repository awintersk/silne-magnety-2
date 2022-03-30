odoo.define('barcode_manager_customization.secondary_body', function (require) {
    'use strict'

    const {bus} = require('web.core')
    const OwlDialog = require('web.OwlDialog')

    const {Component, useState} = owl
    const {onPatched, onMounted} = owl.hooks

    function useWatchDog({state, field, callback, equal = false}) {
        const component = Component.current
        let value = state[field]

        onMounted(() => {
            value = state[field]
        })

        onPatched(() => {
            const isChanged = value !== state[field]
            if (equal ? !isChanged : isChanged) {
                callback.apply(component)
            }
            value = state[field]
        })
    }

    /**
     * @typedef {{
     *   packageItems: {id: Number, name: String, packaging_id: Array<Number|String>}[]|[],
     *   packageTypeItems: {id: Number, name: String, packing_type: String}[]|[],
     *   boxIntId: Number|String,
     *   packageTypeIntId: Number|String,
     * }} SecondaryBodyState
     */

    /**@type {{NEW: 0, NONE: -1}}*/
    const RECORD_ID_CODE = {NONE: -1, NEW: 0}

    /**
     * @extends Component
     */
    class SecondaryBody extends Component {
        setup() {
            /**@type{SecondaryBodyState}*/
            this.state = useState({
                packageItems: [],
                packageTypeItems: [],
                boxIntId: 0,
                packageTypeIntId: 0,
            })
            this.eventSetup()
            useWatchDog({
                state: this.state,
                field: 'boxIntId',
                callback: this._onChangePackage,
            })
        }

        eventSetup() {
            bus.on('barcode_scanned', this, this._onBarcodeScanned)
        }

        eventDestroy() {
            bus.off('barcode_scanned', this, this._onBarcodeScanned)
        }

        async willStart() {
            await this.fetchPackage()
            this.state.packageItems = await this.rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [
                    ['name', 'ilike', `${this.props.item.name}-%%`],
                    ['packaging_id', 'in', this.state.packageTypeItems.map(el => el.id)]
                ],
                fields: ['name', 'packaging_id'],
                orderBy: [{name: 'id', asc: false}]
            })
        }

        /**
         * Update this.state.packageTypeItems
         * @return {Promise<void>}
         */
        async fetchPackage() {
            this.state.packageTypeItems = [{id: 0, name: ''}, ...await this.rpc({
                model: 'product.packaging',
                method: 'search_read',
                domain: [['packing_type', '=', 'box']],
                fields: ['name', 'packing_type', 'weight']
            })]
        }

        /**@return {Boolean}*/
        get packageTypeActive() {
            return Number(this.state.boxIntId) === RECORD_ID_CODE.NEW
        }

        /**@return {String}*/
        get dialogSize() {
            return this.props.product && this.props.product.display_name.length >= 60 ? 'large' : 'medium'
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
                fields: ['id', 'packaging_id']
            })
            if (packageId) {
                this.state.packageTypeIntId = packageId.packaging_id ? packageId.packaging_id[0] : 0
                this.state.boxIntId = packageId.id
            } else {
                this.state.boxIntId = 0
                this.state.packageTypeIntId = 0

                this.env.services.notification.notify({
                    type: 'danger',
                    title: 'Barcode',
                    message: `Package with barcode: <strong>${barcode}</strong> is not found!`
                })
            }
        }

        _onChangePackage() {
            const boxId = Number(this.state.boxIntId)

            /**@type{{packaging_id: Array<Number | String>}}*/
            const item = this.state.packageItems.find(el => el.id === boxId)

            if (boxId > 0 && item && item.packaging_id) {
                this.state.packageTypeIntId = item.packaging_id[0]
            } else {
                this.state.packageTypeIntId = 0
            }
        }

        onClose() {
            this.destroy()
        }

        onValidate() {
            this.trigger('secondary-body-validate', {
                item: Object.assign({}, this.props.item, {
                    boxIntId: Number(this.state.boxIntId),
                    packageTypeIntId: Number(this.state.packageTypeIntId)
                })
            })
            this.destroy()
        }

        destroy() {
            this.eventDestroy()
            super.destroy()
        }
    }

    Object.assign(SecondaryBody, {
        template: 'barcode_manager_customization.receipt_secondary_body',
        components: {Dialog: OwlDialog}
    })

    return {SecondaryBody, useWatchDog, RECORD_ID_CODE}
});