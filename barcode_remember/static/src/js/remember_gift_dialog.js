odoo.define('barcode_remember.remember_gift_dialog', function (require) {
    'use strict'

    const patchMixin = require('web.patchMixin')
    const Dialog = require('web.OwlDialog');
    const {Component, tags, useState} = owl

    /**
     * @typedef {Object} RememberGiftDialogState
     * @property {Array} productList
     * @property {Object} productId
     */

    class RememberGiftDialog extends Component {
        setup() {
            /**@type{RememberGiftDialogState}*/
            this.state = useState({
                productList: [],
                productId: {},
            })
        }

        async willStart() {
            this.state.productList = await this.rpc({
                model: 'product.template',
                method: 'search_read',
                args: [[['is_gift', '=', true], ['sale_ok', '=', true]]],
                kwargs: {
                    limit: 100,
                }
            })
            if (this.state.productList.length) {
                this.state.productId = this.state.productList[0]
            }
        }

        mounted() {
            this.trigger('listen_to_barcode_scanned', {'listen': false});
        }

        _onCloseDialog() {
            this.destroy()
        }

        _onAddLine() {
            this.trigger('add_gift_product', {id: 0})
            this.destroy()
        }

        destroy() {
            this.trigger('listen_to_barcode_scanned', {'listen': true});
            super.destroy()
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
            <select class="o_input py-1 px-2 mt-3" t-model.number="state.productId.id">
                <t t-foreach="state.productList" t-as="productId" t-key="productId.id">
                    <option t-att-value="productId.id"
                            t-esc="productId.name"
                            t-att-selected="productId.id === state.productId.id"/>
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