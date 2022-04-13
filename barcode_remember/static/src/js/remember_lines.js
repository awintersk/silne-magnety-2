odoo.define('barcode_remember.remember_lines', function (require) {
    'use strict'

    const LinesWidget = require('stock_barcode.LinesWidget');
    const GiftDialog = require('barcode_remember.remember_gift_dialog')
    const {LanguageWarningDialog} = require('barcode_remember.remember_lang_warning_dialog')
    const {ComponentWrapper} = require('web.OwlCompatibility')
    const {PackageWeightDialog} = require('barcode_remember.remember_package_weight')

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
            this.sequenceCode = initialState.picking_sequence_code
            this.containGiftProduct = parent.containGiftProduct
            this.containLangWarningProduct = parent.containLangWarningProduct
            this.useWarningFunc = this.sequenceCode === 'PICK' && model === 'stock.picking' && mode === 'internal'
            /**@returns {{containGift: Boolean, containLang: Boolean}}*/
            this.computeWarningDialogData = () => {
                return {
                    containGift: parent._containGiftProduct(parent.pages),
                    containLang: parent._containLangWarningProduct(parent.pages)
                }
            }
        },

        async _renderLines() {
            await this._super.apply(this, arguments)
            const {containGift, containLang} = this.computeWarningDialogData()
            this.containGiftProduct = containGift
            this.containLangWarningProduct = containLang
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
            } else {
                await dialog(PackageWeightDialog, {pickingID: this.res_id})
                return true
            }
        },
    })

});