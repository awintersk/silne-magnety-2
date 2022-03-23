odoo.define('barcode_remember.remember_action', function (require) {
    'use strict'

    const ClientAction = require('stock_barcode.picking_client_action')

    ClientAction.include({
        custom_events: Object.assign({}, ClientAction.prototype.custom_events, {
            add_gift_product: '_onAddGiftProduct',
        }),

        init() {
            this._super.apply(this, arguments)
            this.containGiftProduct = false
        },

        /**
         * @param {Array} pages
         * @returns {Boolean}
         * @private
         */
        _getContainGiftProduct(pages) {
            return pages.flatMap(item => item.lines).some(item => item.is_gift_product)
        },

        _makePages() {
            const response = this._super.apply(this, arguments)
            this.containGiftProduct = this._getContainGiftProduct(response)
            this.headerWidget.updateRememberState({
                includeGift: this.containGiftProduct,
            })
            this.headerWidget.renderElement()
            return response
        },

        async _onAddGiftProduct({data}) {
            await this._rpc({
                model: 'stock.picking',
                method: 'add_gift_line',
                args: [[this.initialState.id]],
                kwargs: {
                    product: Number(data.id)
                }
            })
            this.trigger_up('reload')
        },
    })

});