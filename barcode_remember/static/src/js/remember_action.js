odoo.define('barcode_remember.remember_action', function (require) {
    'use strict'

    const ClientAction = require('stock_barcode.picking_client_action')

    ClientAction.include({
        custom_events: Object.assign({}, ClientAction.prototype.custom_events, {
            add_gift_product: '_onAddGiftProduct',
            add_warning_product: '_onAddLangWarningProduct',
        }),

        init() {
            this._super.apply(this, arguments)
            this.containGiftProduct = false
            this.containLangWarningProduct = false
        },

        /**
         * @param {Array} pages
         * @returns {Boolean}
         * @private
         */
        _containGiftProduct(pages) {
            return pages.flatMap(item => item.lines).some(item => item.is_gift_product)
        },

        /**
         * @param {Array} pages
         * @returns {Boolean}
         * @private
         */
        _containLangWarningProduct(pages) {
            return pages.flatMap(item => item.lines).some(item => item.is_lang_warning_product)
        },

        _makePages() {
            const response = this._super.apply(this, arguments)
            this.containGiftProduct = this._containGiftProduct(response)
            this.containLangWarningProduct = this._containLangWarningProduct(response)
            this.headerWidget.updateRememberState({
                includeGift: this.containGiftProduct,
                includeLangWarning: this.containLangWarningProduct,
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

        async _onAddLangWarningProduct({data}) {
            await this._rpc({
                model: 'stock.picking',
                method: 'add_product_warning_line',
                args: [[this.initialState.id]],
                kwargs: {
                    product: Number(data.id)
                }
            })
            this.trigger_up('reload')
        },
    })

});