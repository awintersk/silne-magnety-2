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
            const {initialState} = parent
            const {model, mode} = this
            this.res_id = initialState.id
            this.containGiftProduct = this.page.lines.some(item => item.is_gift_product)
            this.containLangWarningProduct = this.page.lines.some(item => item.is_lang_warning_product)
            this.sequenceCode = initialState.picking_sequence_code
            this.useWarningFunc = this.sequenceCode === 'PICK' && model === 'stock.picking' && mode === 'internal'
        },

        async _renderLines() {
            await this._super.apply(this, arguments)
            this.containGiftProduct = this.page.lines.some(item => item.is_gift_product)
            this.containLangWarningProduct = this.page.lines.some(item => item.is_lang_warning_product)
        },

        /**
         * @param {MouseEvent} event
         * @private
         */
        async _onClickValidatePage(event) {
            event.stopPropagation()
            const _super = this._super
            if (this.useWarningFunc) {
                const is_warning_open = await this._openWarningDialog()
                if (is_warning_open) {
                    return undefined
                }
            }
            _super.apply(this, arguments)
        },

        /**
         * @returns {Promise<Boolean>}
         * @private
         */
        async _openWarningDialog() {
            const dialog = async (comp, props) => await new ComponentWrapper(this, comp, props).mount(this.el)
            if (!this.containGiftProduct) {
                await dialog(GiftDialog, {})
                return true
            } else if (!this.containLangWarningProduct) {
                await dialog(LanguageWarningDialog, {pickingID: this.res_id})
                return true
            }
            return false
        },
    })

});