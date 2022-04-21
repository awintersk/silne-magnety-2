odoo.define('barcode_manager_customization.lines_widget', function (require) {
    'use strict'

    const Dialog = require('web.Dialog')
    const LinesWidget = require('stock_barcode.LinesWidget')

    const {_t} = require('web.core')

    LinesWidget.include({
        events: Object.assign({}, LinesWidget.prototype.events, {
            'click .o_create_backorder': '_onCreateBackorder',
        }),

        /**
         * @returns {Boolean}
         * @private
         */
        _isPutInPackDisabled() {
            /**@type{{mode: String, dontShowOrderPopup: Number[], currentState: {barcode_sale_order_ids: Object<*>[]}}}*/
            const parentWidget = this.getParent()
            const orderIds = parentWidget.currentState.barcode_sale_order_ids || []

            if (parentWidget.mode !== 'receipt') return false;
            if (!orderIds.length) return false;

            return !(parentWidget.dontShowOrderPopup.length === this.page.lines.length)
        },

        /**
         * @returns {Promise<*>}
         * @private
         */
        async _createBackorder() {
            return await this._rpc({
                model: 'stock.picking',
                method: 'create_backorder',
                args: [this.getParent().currentState.id],
            })
        },

        async _onCreateBackorder() {
            const dialog = new Dialog(this, {
                title: _t('Confirmation'),
                size: 'medium',
                $content: $(`<span>${_t('Do you really confirm the creation of backorder?')}</span>`),
                buttons: [
                    {
                        close: true,
                        classes: 'btn btn-primary',
                        text: _t('Cancel')
                    },
                    {
                        close: true,
                        classes: 'btn btn-secondary',
                        text: _t('Confirm'),
                        click: async () => {
                            await this._createBackorder()
                            this.trigger_up('exit')
                            this.do_action('stock_barcode.stock_picking_type_action_kanban')
                        }
                    }
                ],
            })
            dialog.open({shouldFocusButtons: true})
        },

        _handleControlButtons() {
            this._super.apply(this, arguments)
            this.$('.o_put_in_pack').attr('disabled', this._isPutInPackDisabled())
        },
    })

});