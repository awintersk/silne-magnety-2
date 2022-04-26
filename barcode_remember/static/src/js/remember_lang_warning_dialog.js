odoo.define('barcode_remember.remember_lang_warning_dialog', function (require) {
    'use strict'

    const {catchCommandBarcode} = require('barcode_remember.remember_tools')
    const patchMixin = require('web.patchMixin')
    const Dialog = require('web.OwlDialog')
    const {bus} = require('web.core')
    const {Component, tags, useState} = owl

    /**
     * @typedef {Object} RememberLanguageWarningDialogState
     * @property {Object} country
     * @property {Object[]} productList
     * @property {RememberLanguageWarningDialogProduct} productId
     */

    /**
     * @typedef {Object} RememberLanguageWarningDialogProduct
     * @property {String} name
     * @property {Number, String} id
     * @property {String} [barcode]
     */

    /**
     * @property {RememberLanguageWarningDialogState} state
     * @property {{pickingID: Number}} props
     */
    class RememberLanguageWarningDialog extends Component {
        setup() {
            this.state = useState({
                country: {},
                productList: [],
                productId: {},
            })
        }

        async willStart() {
            const response = await this.rpc({
                route: '/barcode_remember/warning/country', params: {
                    picking: this.props.pickingID
                }
            })
            this.state.country = response.country
            this.state.productList = await this.rpc({
                model: 'product.product',
                method: 'search_read',
                args: [[['is_lang_warning', '=', true], ['sale_ok', '=', true]]],
                kwargs: {
                    fields: ['name', 'barcode'],
                    limit: 100,
                }
            })
            if (this.state.productList.length) {
                this.state.productId = this.state.productList[0]
            }
        }

        mounted() {
            this.trigger('listen_to_barcode_scanned', {'listen': false});
            bus.on('barcode_scanned', this, this._onBarcodeScannedHandler);
        }

        get notification() {
            return this.env.services.notification
        }

        /**
         * @param {String} barcode
         * @private
         */
        _onBarcodeScannedHandler(barcode) {
            const useExit = catchCommandBarcode(barcode, {
                validate: () => this._onValidate(),
                discard: () => this.destroy(),
            })

            if (useExit) {
                return
            }

            const productId = this.state.productList.find(item => item.barcode === barcode)

            if (productId) {
                this.state.productId = productId
                this.notification.notify({
                    title: `Selected product with barcode"${barcode}"`,
                    type: 'success'
                })
            } else {
                this.notification.notify({
                    title: `Product with barcode "${barcode} not found"`,
                    type: 'danger'
                })
            }
        }

        _onCloseDialog() {
            this.destroy()
        }

        _onValidate() {
            this.trigger('add_warning_product', {id: this.state.productId.id})
            this.destroy()
        }

        willUnmount() {
            this.trigger('listen_to_barcode_scanned', {'listen': true});
            bus.off('barcode_scanned', this, this._onBarcodeScannedHandler);
        }
    }

    RememberLanguageWarningDialog.components = {Dialog}
    RememberLanguageWarningDialog.props = {
        pickingID: Number
    }
    RememberLanguageWarningDialog.template = tags.xml`
    <Dialog t-on-dialog-closed="_onCloseDialog" title="'Language Warning'" size="'small'">
        <div class="d-flex flex-column text-center">
            <img t-attf-src="{{state.country.image_url}}"
                 t-if="state.country.id"
                 class="o_barcode_icon"
                 alt="Barcode"
                 height="70"
                 style="object-fit: contain;"/>
             <br/>
            <span class="d-flex flex-column justify-content-center">
                <span t-if="state.country.id">
                    <i class="fa fa-map"/>
                    <b class="pl-2">Country</b>: <t t-esc="state.country.name"/>
                </span>
            </span>
            <div class="d-flex flex-column justify-content-center mt-4">
                <b>Scan product barcode or use bellow button</b>
                <select class="o_input py-1 px-2 mt-3" t-model="state.productId.id" t-if="state.productList.length">
                    <t t-foreach="state.productList" t-as="productId" t-key="productId.id">
                        <option t-att-value="productId.id" t-esc="productId.name"/>
                    </t>
                </select>
                <span t-else="" class="mt-2">
                    Product with type "Language Warning" not exists.
                </span>
            </div>
        </div>
        <t t-set-slot="buttons">
            <button class="btn btn-primary w-100" t-on-click="_onValidate">Add a Language Warning product</button>
        </t>
    </Dialog>
    `

    return {LanguageWarningDialog: patchMixin(RememberLanguageWarningDialog)}
});