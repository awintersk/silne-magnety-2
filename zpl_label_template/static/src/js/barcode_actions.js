odoo.define('zpl_label_template.barcode_actions', function (require) {
    'use strict'

    const SettingsWidget = require('stock_barcode.SettingsWidget')
    const PickingClientAction = require('stock_barcode.picking_client_action')
    const {ComponentWrapper} = require('web.OwlCompatibility');
    const {ProductPrintLabelZPL, BoxPrintLabelZPL, PalletPrintLabelZPL} = require('zpl_label_template.barcode')

    SettingsWidget.include({
        events: Object.assign({}, SettingsWidget.prototype.events, {
            'click .o_print_product_labels_zpl': '_onPrintProductLabel',
            'click .o_print_box_labels_zpl': '_onPrintBoxLabel',
            'click .o_print_pallet_labels_zpl': '_onPrintPalletLabel',
        }),

        /**
         * @param {jQuery.Event} event
         * @private
         */
        _onPrintProductLabel(event) {
            event.stopPropagation()
            this.trigger_up('print_product_zpl')
        },

        /**
         * @param {jQuery.Event} event
         * @private
         */
        _onPrintBoxLabel(event) {
            event.stopPropagation()
            this.trigger_up('print_box_zpl')
        },

        /**
         * @param {jQuery.Event} event
         * @private
         */
        _onPrintPalletLabel(event) {
            event.stopPropagation()
            this.trigger_up('print_pallet_zpl')
        },
    })

    PickingClientAction.include({
        custom_events: Object.assign({}, PickingClientAction.prototype.custom_events, {
            'print_product_zpl': '_onPrintProductZPL',
            'print_box_zpl': '_onPrintBoxZPL',
            'print_pallet_zpl': '_onPrintPalletZPL'
        }),

        /**
         * @private
         */
        _onPrintProductZPL() {
            this.mutex.exec(async () => {
                await this._save()
                const component = new ComponentWrapper(this, ProductPrintLabelZPL, {
                    lines: this.linesWidget.page.lines
                })
                await component.mount(this.el)
            })
        },

        /**
         * @private
         */
        _onPrintBoxZPL() {
            this.mutex.exec(async () => {
                await this._save()
                const component = new ComponentWrapper(this, BoxPrintLabelZPL, {
                    lines: this.linesWidget.page.lines
                })
                await component.mount(this.el)
            })
        },

        /**
         * @private
         */
        _onPrintPalletZPL() {
            this.mutex.exec(async () => {
                await this._save()
                const component = new ComponentWrapper(this, PalletPrintLabelZPL, {
                    lines: this.linesWidget.page.lines
                })
                await component.mount(this.el)
            })
        }
    })
});