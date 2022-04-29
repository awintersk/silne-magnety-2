odoo.define('barcode_remember.remember_gift_dialog', function (require) {
    'use strict'

    const {catchCommandBarcode} = require('barcode_remember.remember_tools')
    const patchMixin = require('web.patchMixin')
    const Dialog = require('web.OwlDialog')
    const {bus} = require('web.core')

    const {Component, tags, useState} = owl

    /**
     * @typedef {Object} RememberGiftDialogState
     * @property {RememberGiftDialogProduct[]} productList
     * @property {RememberGiftDialogProduct} productId
     */

    /**
     * @typedef {Object} RememberGiftDialogProduct
     * @property {String} name
     * @property {Number, String} id
     * @property {String} [barcode]
     */

    if (odoo.debug === '1' && !window.barcodeScanner) {
        const scan = barcode => {
            bus.trigger('barcode_scanned', barcode)
        }
        window.barcodeScanner = {scan}
    }

    /**
     * @property {RememberGiftDialogState} state
     */
    class RememberGiftDialog extends Component {
        setup() {
            this.state = useState({
                productList: [],
                productId: {},
            })
        }

        async willStart() {
            this.state.productList = await this.rpc({
                model: 'product.product',
                method: 'search_read',
                args: [[['is_gift', '=', true], ['sale_ok', '=', true]]],
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

        _onCloseDialog() {
            this.destroy()
        }

        _onAddLine() {
            this.trigger('add_gift_product', {id: this.state.productId.id})
            this.destroy()
        }

        /**
         * @param {String} barcode
         * @private
         */
        _onBarcodeScannedHandler(barcode) {
            const useExit = catchCommandBarcode(barcode, {
                validate: () => this._onAddLine(),
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

        willUnmount() {
            this.trigger('listen_to_barcode_scanned', {'listen': true});
            bus.off('barcode_scanned', this, this._onBarcodeScannedHandler);
        }
    }

    RememberGiftDialog.components = {Dialog}
    RememberGiftDialog.template = tags.xml`
    <Dialog t-on-dialog-closed="_onCloseDialog" title="'Do not forget put gift product'" size="'small'">
        <div class="d-flex flex-column text-center">
            <img src="/stock_barcode/static/img/barcode.svg"
                 class="o_barcode_icon"
                 alt="Barcode"
                 height="70"
                 style="object-fit: contain;"/>
             <br/>
            <b>Scan product barcode or use bellow button</b>
            <select class="o_input py-1 px-2 mt-3" t-model="state.productId.id">
                <t t-foreach="state.productList" t-as="productId" t-key="productId.id">
                    <option t-att-value="productId.id" t-esc="productId.name"/>
                </t>
            </select>
        </div>
        <t t-set-slot="buttons">
            <button class="btn btn-primary w-100"
                    t-att-disabled="!(state.productId.id > 0)"
                    t-on-click="_onAddLine">Add a gift product</button>
        </t>
    </Dialog>
    `

    return patchMixin(RememberGiftDialog)
});