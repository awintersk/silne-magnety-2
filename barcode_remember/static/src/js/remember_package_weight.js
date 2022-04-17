odoo.define('barcode_remember.remember_package_weight', function (require) {
    'use strict'

    const OwlDialog = require('web.OwlDialog')
    const patchMixin = require('web.patchMixin')

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
        }

        async willStart() {
            this.state.packageList = await this.rpc({
                route: '/barcode_remember/package/weight_data',
                params: {
                    picking: this.props.pickingID,
                }
            })
        }

        mounted() {
            if (!this.state.packageList.length) {
                this.__validate()
                this.destroy()
            }
        }

        onClose() {
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
            this.__validate()
            this.destroy()
        }

        __validate() {
            this.trigger('validate', {preventDialog: true})
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