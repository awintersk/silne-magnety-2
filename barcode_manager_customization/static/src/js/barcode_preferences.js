odoo.define('barcode_manager_customization.barcode_preferences', function (require) {
    'use strict'

    const OwlDialog = require('web.OwlDialog')
    const patchMixin = require('web.patchMixin')

    const {Component, useState} = owl


    /**
     * @extends Component
     */
    class BarcodePreferencesDialog extends Component {
        setup() {
            this.state = useState({
                usePickingDialog: {
                    name: 'barcode_manager_customization.use_barcode_picking_dialog',
                    value: false,
                },
            })
        }

        async willStart() {
            this.state.usePickingDialog.value = await this.getParam(this.state.usePickingDialog.name)
        }

        /**
         * @param {String} name
         * @returns {Promise<*>}
         */
        getParam(name) {
            return this.rpc({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: [name],
            })
        }

        /**
         * @param {String} name
         * @param {String|Number|Boolean} value
         * @returns {Promise<*>}
         */
        setParam({name, value}) {
            return this.rpc({
                model: 'ir.config_parameter',
                method: 'set_param',
                args: [name, value],
            })
        }

        get notification() {
            return this.env.services.notification
        }

        onClose() {
            this.destroy()
        }

        async onSave() {
            await this.setParam(this.state.usePickingDialog)
            this.notification.notify({
                message: 'Saved',
                type: 'info',
            });
            this.destroy()
        }

        /**
         * @param {String} field
         * @returns {String}
         */
        buttonClass(field) {
            const flexClass = 'd-flex align-items-center justify-content-center'
            return `btn btn-${this.state[field].value ? 'primary' : 'secondary'} ${flexClass}`
        }

        /**
         * @param {String} field
         */
        toggleValue(field) {
            this.state[field].value = !this.state[field].value
        }

    }

    Object.assign(BarcodePreferencesDialog, {
        template: 'barcode_manager_customization.BarcodePreferencesDialog',
        components: {Dialog: OwlDialog}
    })

    return {BarcodePreferencesDialog: patchMixin(BarcodePreferencesDialog)}
});