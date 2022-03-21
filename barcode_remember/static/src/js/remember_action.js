odoo.define('barcode_remember.remember_action', function (require) {
    'use strict'

    const ClientAction = require('stock_barcode.ClientAction')

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

        _onAddGiftProduct({data}) {
            console.log(data)
        },
    })

});