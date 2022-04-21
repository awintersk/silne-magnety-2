odoo.define('barcode_remember.remember_action', function (require) {
    'use strict'

    const ClientAction = require('stock_barcode.picking_client_action')
    const GiftDialog = require('barcode_remember.remember_gift_dialog')
    const {LanguageWarningDialog} = require('barcode_remember.remember_lang_warning_dialog')
    const {ComponentWrapper} = require('web.OwlCompatibility')
    const {PackageWeightDialog} = require('barcode_remember.remember_package_weight')

    ClientAction.include({
        custom_events: Object.assign({}, ClientAction.prototype.custom_events, {
            add_gift_product: '_onAddGiftProduct',
            add_warning_product: '_onAddLangWarningProduct',
        }),

        init() {
            this._super.apply(this, arguments)
            this.containGiftProduct = false
            this.containLangWarningProduct = false
            this.sequenceCode = ''
            this.useWarningFunc = false
        },

        async willStart() {
            const response = await this._super.apply(this, arguments)
            const {mode} = this
            const {model} = this.actionParams
            this.sequenceCode = this.initialState.picking_sequence_code
            this.useWarningFunc = this.sequenceCode === 'PICK' && model === 'stock.picking' && mode === 'internal'
            return response
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

        /**
         * @param {MouseEvent} event
         * @private
         */
        async _onValidate(event) {
            event.stopPropagation()
            /**@type{Boolean}*/
            const preventDialog = event.data.preventDialog
            /**@type{Function}*/
            const superOnValidate = this._super.bind(this)

            if (this.useWarningFunc && !preventDialog) {
                if (await this._openWarningDialog()) {
                    return undefined
                }
            }

            superOnValidate(...arguments)
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
                await dialog(LanguageWarningDialog, {pickingID: this.initialState.id})
                return true
            } else {
                await dialog(PackageWeightDialog, {pickingID: this.initialState.id})
                return true
            }
        },
    })

});