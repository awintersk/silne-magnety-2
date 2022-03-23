odoo.define('barcode_remember.remember_lines', function (require) {
    'use strict'

    const LinesWidget = require('stock_barcode.LinesWidget');
    const GiftDialog = require('barcode_remember.remember_gift_dialog')
    const {LanguageWarningDialog} = require('barcode_remember.remember_lang_warning_dialog')
    const {ComponentWrapper} = require('web.OwlCompatibility')

    /**
     * @name LinesWidget
     * @property {Object[]} page.lines
     */
    LinesWidget.include({

        init: function (parent, page, pageIndex, nbPages) {
            this._super.apply(this, arguments)
            this.res_id = parent.initialState.id
            this.containGiftProduct = this.page.lines.some(item => item.is_gift_product)
        },

        async _renderLines() {
            await this._super.apply(this, arguments)
            this.containGiftProduct = this.page.lines.some(item => item.is_gift_product)
        },

        /**
         * @param {MouseEvent} event
         * @private
         */
        async _onClickValidatePage(event) {
            event.stopPropagation()
            if (!this.containGiftProduct) {
                await new ComponentWrapper(this, GiftDialog, {}).mount(this.el)
                return undefined
            } else {
                await new ComponentWrapper(this, LanguageWarningDialog, {pickingID: this.res_id}).mount(this.el)
            }
        },
    })

});