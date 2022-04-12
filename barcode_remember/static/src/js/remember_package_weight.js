odoo.define('barcode_remember.remember_package_weight', function (require) {
    'use strict'

    const OwlDialog = require('web.OwlDialog')
    const patchMixin = require('web.patchMixin')

    const {Component, useState} = owl


    /**
     * @extends Component
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

        onClose() {
            this.destroy()
        }

        async onSave() {
            const packageList = this.state.packageList.map(item => [item.id, item.shipping_weight])
            await this.rpc({
                route: '/barcode_remember/package/weight_set',
                params: {
                    package_list: packageList,
                }
            })
            this.trigger('validate')
            this.destroy()
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