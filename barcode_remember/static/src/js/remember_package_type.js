odoo.define('barcode_remember.remember_package_type', function (require) {
    'use strict'

    const OwlDialog = require('web.OwlDialog')
    const patchMixin = require('web.patchMixin')
    const {catchCommandBarcode, useBarcodeScanner} = require('barcode_remember.remember_tools')
    const {Component, useState} = owl

    /**
     * @typedef {{
     *     id:Number,
     *     name: String,
     *     packagingID: String|Number,
     * }} PackageTypeDialogPackageItem
     */

    /**
     * @typedef {{
     *     id:Number,
     *     name: String,
     *     barcode: String,
     * }} PackageTypeDialogPackagingItem
     */

    /**
     * @typedef {{
     *     packageList: PackageTypeDialogPackageItem[],
     *     packagingList: PackageTypeDialogPackagingItem[],
     * }} PackageTypeDialogState
     */

    /**
     * @extends Component
     * @property {PackageTypeDialogState} state
     */
    class PackageTypeDialog extends Component {
        setup() {
            this.state = useState({
                packageList: []
            })
            useBarcodeScanner(this._onBarcodeScannedHandler)
        }

        async willStart() {
            const packageList = await this.rpc({
                route: '/barcode_remember/package',
                params: {
                    picking: this.props.pickingID,
                }
            })
            for (const item of packageList) {
                item.packagingID = item.packaging_id[0]
                delete item.packaging_id
            }
            this.state.packageList = packageList
            this.state.packagingList = await this.rpc({
                model: 'product.packaging',
                method: 'search_read',
                domain: [],
                fields: ['name', 'barcode'],
            })
        }

        mounted() {
            if (!this.state.packageList.length) {
                this.setConfirmationValue(true)
                this.trigger('validate')
                this.destroy()
            }
        }

        get notification() {
            return this.env.services.notification
        }

        onClose() {
            this.setConfirmationValue(false)
            this.destroy()
        }

        async onSave() {
            for (const item of this.state.packageList) {
                await this.rpc({
                    model: 'stock.quant.package',
                    method: 'write',
                    args: [item.id, {
                        packaging_id: Number(item.packagingID)
                    }],
                })
            }
            this.setConfirmationValue(true)
            this.notification.notify({
                title: `Packaging saved`,
                type: 'success'
            })
            this.destroy()
        }

        /**
         * @param {Boolean} active
         */
        setConfirmationValue(active) {
            this.trigger('change_confirmed_package_type', {confirmed: active})
        }

        /**
         * @param {String} barcode
         * @private
         */
        _onBarcodeScannedHandler(barcode) {
            const useExit = catchCommandBarcode(barcode, {
                validate: () => this.onSave(),
                discard: () => this.onClose(),
                cancel: () => this.onClose(),
            })

            if (useExit) {
                return undefined;
            }

            const packaging = this.state.packagingList.find(
                item => item.barcode === barcode || item.name === barcode
            )

            if (packaging) {
                for (const item of this.state.packageList) {
                    item.packagingID = packaging.id
                }
                this.notification.notify({
                    title: `Selected: ${packaging.name}.`,
                    type: 'info'
                })
            } else {
                this.notification.notify({
                    title: `Delivery package not found.`,
                    type: 'danger'
                })
            }
        }
    }

    Object.assign(PackageTypeDialog, {
        template: 'barcode_remember.PackageTypeDialog',
        components: {Dialog: OwlDialog},
        props: {
            pickingID: Number,
        }
    })

    return {PackageTypeDialog: patchMixin(PackageTypeDialog)}
});