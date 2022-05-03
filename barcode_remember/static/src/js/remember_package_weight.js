odoo.define('barcode_remember.remember_package_weight', function (require) {
    'use strict'

    const OwlDialog = require('web.OwlDialog')
    const patchMixin = require('web.patchMixin')
    const {round} = require('barcode_manager_customization.BarcodeInternalDialog')
    const {catchCommandBarcode, useBarcodeScanner} = require('barcode_remember.remember_tools')
    const {Component, useState} = owl

    /**
     * @typedef {{
     *     shipping_weight: Number,
     *     name: String,
     *     weight_uom_name: String,
     *     weight: Number,
     * }} PackageWeightDialogPackageItem
     */

    /**
     * @typedef {{
     *     packageList: PackageWeightDialogPackageItem[]
     * }} PackageWeightDialogState
     */

    /**
     * @extends Component
     * @property {PackageWeightDialogState} state
     */
    class PackageWeightDialog extends Component {
        setup() {
            this.state = useState({
                packageList: []
            })
            useBarcodeScanner(this._onBarcodeScannedHandler)
        }

        async willStart() {
            const packageList = await this.rpc({
                route: '/barcode_remember/package/weight_data',
                params: {
                    picking: this.props.pickingID,
                }
            })
            for (let packageItem of packageList) {
                packageItem['weight'] = round(packageItem['weight'], 4)
            }
            this.state.packageList = packageList
        }

        mounted() {
            if (!this.state.packageList.length) {
                this._validate()
                this.destroy()
            }
        }

        onClose() {
            this.trigger('change_confirmed_package_weight', {confirmed: false})
            this.destroy()
        }

        async onSave() {
            const packageList = this.state.packageList.map(item => [item.id, item.shipping_weight])
            if (packageList.length) {
                await this.rpc({
                    route: '/barcode_remember/package/weight_set',
                    params: {
                        package_list: packageList,
                    }
                })
            }
            this._validate()
            this.destroy()
        }

        _validate() {
            this.trigger('change_confirmed_package_weight', {confirmed: true})
            this.trigger('validate')
        }

        /**
         * @param {String} barcode
         * @private
         */
        _onBarcodeScannedHandler(barcode) {
            catchCommandBarcode(barcode, {
                validate: () => this.onSave(),
                discard: () => this.onClose(),
                cancel: () => this.onClose(),
            })
        }
    }

    Object.assign(PackageWeightDialog, {
        template: 'barcode_remember.PackageWeightDialog',
        components: {Dialog: OwlDialog},
        props: {
            pickingID: Number,
        }
    })

    return {PackageWeightDialog: patchMixin(PackageWeightDialog)}
});