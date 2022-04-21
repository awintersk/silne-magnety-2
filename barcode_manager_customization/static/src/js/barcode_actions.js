odoo.define('zpl_label_template.barcode_actions', function (require) {
    'use strict'

    const SettingsWidget = require('stock_barcode.SettingsWidget')
    const {ComponentWrapper} = require('web.OwlCompatibility');
    const {BarcodePreferencesDialog} = require('barcode_manager_customization.barcode_preferences')

    SettingsWidget.include({
        events: Object.assign({}, SettingsWidget.prototype.events, {
            'click .o_barcode_preferences': '_onOpenBarcodePreferences',
        }),

        /**
         * @param {jQuery.Event} event
         * @private
         */
        async _onOpenBarcodePreferences(event) {
            event.stopPropagation()
            const dialog = new ComponentWrapper(this, BarcodePreferencesDialog, {})
            await dialog.mount(document.createDocumentFragment())
        },
    })
});