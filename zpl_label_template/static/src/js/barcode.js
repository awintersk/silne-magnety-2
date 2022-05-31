odoo.define('zpl_label_template.barcode', function (require) {
    'use strict'

    const Dialog = require('web.OwlDialog')

    const {Component} = owl
    const {useRef, useState} = owl.hooks

    class _DialogComponent extends Component {
        constructor(parent, props) {
            super(parent, props);
        }

        setup() {
            this.dialog = useRef('dialog')
        }

        _onDialogClosed() {
            this.destroy()
        }

        _onClose() {
            this.dialog.comp._close()
        }
    }

    class ProductPrintLabelZPL extends _DialogComponent {
        constructor(parent, props) {
            super(parent, props);
            this.state = useState({
                lines: props.lines.map(line => ({
                    product_id: line.product_id.id,
                    name: line.display_name.replace(/(\[.*\])/g, '').trim(),
                    qty: line.product_uom_qty || line.qty_done,
                    printed: false,
                }))
            })
        }

        async _onPrintLine(line) {
            const action = await this.rpc({
                model: 'product.product',
                method: 'actions_print_label_zpl',
                args: [[], line],
            })
            this.trigger('do_action', {
                action: action
            })
            line.printed = true
        }
    }

    class BoxPrintLabelZPL extends _DialogComponent {
        constructor(parent, props) {
            super(parent, props);
            this.state = useState({lines: []})
        }

        async willStart() {
            /**@type{Number[]}*/
            const ids = []

            for (const line of this.props.lines) {
                ids.push(line.package_id[0])
                ids.push(line.result_package_id[0])
            }

            this.state.lines = await this.rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [
                    ['id', 'in', ids],
                    ['packaging_id.packing_type', '=', 'box']
                ],
                fields: ['name']
            })

            this.state.lines.map(line => Object.assign(line, {printed: false}))
        }

        /**
         * @param line
         * @return {Promise<void>}
         * @private
         */
        async _onPrintLine(line) {
            this.trigger('do_action', {
                action: {
                    name: 'Box Label (ZPL)',
                    type: 'ir.actions.report',
                    model: 'stock.quant.package',
                    report_type: 'qweb-text',
                    report_name: 'zpl_label_template.zpl_label_box_view',
                    report_file: 'zpl_label_template.zpl_label_box_view',
                    context: {
                        active_ids: [line.id]
                    }
                }
            })
            line.printed = true
        }
    }

    class PalletPrintLabelZPL extends _DialogComponent {
        setup() {
            this.state = useState({lines: []})
            super.setup()
        }

        async willStart() {
            /**@type{Number[]}*/
            const ids = []

            for (const line of this.props.lines) {
                ids.push(line.package_id[0])
                ids.push(line.result_package_id[0])
            }

            this.state.lines = await this.rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [
                    ['id', 'in', ids],
                    ['packaging_id.packing_type', '=', 'pallet']
                ],
                fields: ['name']
            })

            this.state.lines.map(line => Object.assign(line, {printed: false}))
        }

        /**
         * @param line
         * @return {Promise<void>}
         * @private
         */
        async _onPrintLine(line) {
            await this._rpc({
                model: 'stock.quant.package',
                method: 'print_pallet_via_printnode',
                args: [[line.id]],
            })
            line.printed = true
        }
    }

    ProductPrintLabelZPL.components = {Dialog}
    ProductPrintLabelZPL.defaultProps = {lines: []}
    ProductPrintLabelZPL.props = {lines: Array}
    ProductPrintLabelZPL.template = 'zpl_label_template.ProductPrintLabelZPL'

    BoxPrintLabelZPL.components = {Dialog}
    BoxPrintLabelZPL.defaultProps = {lines: []}
    BoxPrintLabelZPL.props = {lines: Array}
    BoxPrintLabelZPL.template = 'zpl_label_template.BoxPrintLabelZPL'

    Object.assign(PalletPrintLabelZPL, {
        components: {Dialog},
        defaultProps: {lines: []},
        props: {lines: Array},
        template: 'zpl_label_template.PalletPrintLabelZPL',
    })

    return {ProductPrintLabelZPL, BoxPrintLabelZPL, PalletPrintLabelZPL}
});