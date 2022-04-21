odoo.define('barcode_manager_customization.BarcodePackageDialog', function (require) {
    'use strict'

    const AbstractAction = require('web.AbstractAction')
    const Dialog = require('web.Dialog')
    const {_t, action_registry, bus} = require('web.core')
    const {blockUI, unblockUI} = require('web.framework')

    /**
     * @typedef {{
     *  productList: {id: Number, customerName: String, quantity: Number, product_id: {id: Number, name: String}}[]|[],
     *  packageList: {id: Number, name: String}[]|[],
     *  packageIntId: Number,
     *  saleOrderId: {id: Number}|{},
     *  newPackageId: {id: Number}|{},
     *  saved: Boolean,
     *}} PackageBarcodeActionState
     */

    /**
     * @typedef {{
     *  pickingId: {id: Number},
     *  barcode: String,
     *  packageId: {id: Number},
     *  mode: String,
     *}} PackageBarcodeActionContext
     */

    /**
     * @extends AbstractAction
     */
    const PackageBarcodeAction = AbstractAction.extend({
        contentTemplate: 'barcode_manager_customization.barcode_delivery_dialog',

        events: {
            'change #package_select': '_onChangePackage',
            'click button[data-event="print_pdf"]': '_onPrintPdf',
            'click button[data-event="print_zpl"]': '_onPrintZpl',
            'click button[data-event="create_package"]': '_onCreatePackage',
        },

        init(parent, context) {
            this._super.apply(this, arguments)

            /**@type PackageBarcodeActionContext*/
            this.actionContext = context.context

            /**@type PackageBarcodeActionState*/
            this.actionState = {
                productList: [],
                packageList: [],
                packageIntId: 0,
                saleOrderId: {},
                newPackageId: {},
                saved: false,
            }

            this._onSave = this._onSave.bind(this)
            this._onClose = this._onClose.bind(this)
        },

        async willStart() {
            const response = await this._super.apply(this, arguments)

            blockUI()
            try {
                await this._fetchProductList()

                if (!this.actionState.productList.length) {
                    this.displayNotification({
                        title: this.actionContext.barcode,
                        message: _t('The product for the current package does not exist!')
                    })
                    unblockUI()
                }

                await this._fetchPallets()
                await this._fetchOrder()
            } finally {
                unblockUI()
            }

            return response
        },

        on_attach_callback() {
            if (!this.actionState.productList.length) {
                this._onClose()
            } else {
                bus.on('barcode_scanned', this, this._onBarcodeScanned)
            }
        },

        on_detach_callback() {
            bus.off('barcode_scanned', this, this._onBarcodeScanned)
        },

        /**
         * @param {String} packageType='pallet'
         * @returns {Promise<void>}
         * @private
         */
        async _fetchPallets(packageType = 'pallet') {
            if (this.actionContext.mode === 'internal') {
                packageType = 'box'
            }
            this.actionState.packageList = await this._rpc({
                model: 'stock.picking',
                method: 'get_stock_package_json',
                args: [[this.actionContext.pickingId.id], packageType]
            })
        },

        /**
         * @returns {Promise<void>}
         * @private
         */
        async _fetchProductList() {
            const [pickingResponse] = await this._rpc({
                model: 'stock.picking',
                method: 'read',
                args: [[this.actionContext.pickingId.id], ['partner_id']],
            })

            this.actionState.productList = []

            const response = await this._rpc({
                model: 'stock.move.line',
                method: 'search_read',
                domain: [
                    '|',
                    ['picking_id', '=', this.actionContext.pickingId.id],
                    ['result_package_id', '=', this.actionContext.packageId.id],
                    ['package_id', '=', this.actionContext.packageId.id]
                ],
                fields: ['product_id', 'qty_done', 'product_uom_qty', 'package_id', 'result_package_id']
            })

            for (const item of response) {
                if (item.product_uom_qty <= 0) continue;
                if (!item.result_package_id || item.result_package_id[0] === item.package_id[0]) {
                    this.actionState.productList.push({
                        customerName: pickingResponse.partner_id[1],
                        product_id: {id: item.product_id[0], name: item.product_id[1]},
                        quantity: item.product_uom_qty,
                        moveLineIntId: item.id
                    })
                }
            }
        },

        /**
         * @returns {Promise<void>}
         * @private
         */
        async _fetchOrder() {
            const [picking] = await this._rpc({
                model: 'stock.picking',
                method: 'read',
                args: [[this.actionContext.pickingId.id], ['sale_id']]
            })
            if (picking.sale_id) {
                this.actionState.saleOrderId = {id: picking.sale_id[0]}
            }
        },

        /**@returns {HTMLElement|null}*/
        packageSelect() {
            return this.el ? this.el.querySelector('#package_select') : null
        },

        /**@returns {jQuery}*/
        $packageSelect() {
            return $(this.packageSelect())
        },

        /**
         * @param {'receipt'|'internal'|'delivery'} mode
         * @returns {Boolean}
         */
        isMode(mode) {
            return this.actionContext.mode === mode
        },

        /**
         * @param {jQuery} $node
         */
        renderButtons($node) {
            const $buttonCancel = $(`<button class="btn btn-primary mr-auto mr-md-0" data-event="close">${_t('Close')}</button>`)
            const $buttonSave = $(`<button class="btn btn-secondary ml-auto ml-md-2" data-event="save" disabled="">${_t('Move')}</button>`)
            $buttonCancel.on('click', this._onClose)
            $buttonSave.on('click', this._onSave)
            $buttonCancel.appendTo($node)
            $buttonSave.appendTo($node)
            this.$buttons = $node.find('button')
        },

        /**
         * @returns {Promise<void>}
         * @private
         */
        async _put_in_puck_line() {
            /**@type Number*/
            const newPackageIntId = await this._rpc({
                model: 'stock.picking',
                method: 'put_in_pack_line',
                args: [
                    this.actionContext.pickingId.id,
                    this.actionState.productList.map(el => el.moveLineIntId)
                ],
            })
            await this._fetchPallets()
            this.renderElement()
            this.$packageSelect().val(newPackageIntId)
            this._onChangePackage({target: this.packageSelect()})
            this.actionState.newPackageId = {id: newPackageIntId}
            this.$packageSelect().attr('disabled', true)
            this.$el.closest('.modal-content').find('button[data-event="save"]').remove()
            $('.barcode-picking-dialog__print-container').show()
        },

        /**
         * @return {Promise<Number[]|[]>}
         * @private
         */
        async _fetchParentPackage() {
            const {packageIntId} = this.actionState
            const {packageId} = this.actionContext

            const lines = await this._rpc({
                model: 'stock.move.line',
                method: 'search_read',
                domain: [
                    ['result_package_id', '=', packageIntId],
                    ['result_package_id.packaging_id.packing_type', '=', 'pallet'],
                    ['package_id', '!=', false],
                    ['package_id.packaging_id.packing_type', '=', 'box']
                ],
                fields: ['package_id']
            })

            /**@type{Set<Number>}*/
            const packageIntIds = new Set(lines.map(el => el.package_id[0]))

            if (packageId) {
                packageIntIds.add(packageId.id)
            }

            return Array.from(packageIntIds)
        },

        /**
         * @param {Event|{target: HTMLSelectElement}} event
         * @private
         */
        _onChangePackage(event) {
            const value = parseInt(event.target.value)
            const disabled = !Boolean(value)
            this.actionState.packageIntId = value
            this.$('.barcode-picking-dialog__print-container button').attr('disabled', disabled)
            this.$el.closest('.modal-content').find('button[data-event="save"]').attr('disabled', disabled)
        },

        /**
         * @returns {Promise<void>}
         * @private
         */
        async _onCreatePackage() {
            const message = `Do you really want to create a new ${this.isMode('internal') ? 'box' : 'pallet'}?`
            const dialog = new Dialog(this, {
                title: _t('Confirmation'),
                $content: $(`<span>${message}</span>`),
                size: 'medium',
                buttons: [
                    {
                        close: true,
                        classes: 'btn btn-primary',
                        text: _t('Cancel'),
                    },
                    {
                        close: true,
                        classes: 'btn btn-secondary',
                        text: _t('Confirm'),
                        click: () => {
                            this._put_in_puck_line()
                            dialog.close()
                        },
                    }
                ]
            });
            dialog.open({shouldFocusButtons: true})
        },

        _onPrintPdf() {
            this.do_action('stock.action_report_quant_package_barcode', {
                download: true,
                additional_context: {
                    active_ids: [this.actionState.packageIntId]
                }
            })
        },

        _onPrintZpl: async function () {
            this.do_action('zpl_label_template.action_pallet_report', {
                additional_context: {
                    active_ids: [this.actionState.packageIntId]
                }
            })
        },

        /**
         * @param {String} barcode
         * @private
         */
        async _onBarcodeScanned(barcode) {
            const [packageId] = await this._rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [['name', '=', barcode]],
                fields: ['id'],
                limit: 1,
            })
            const $select = this.$('#package_select')
            $select.val(packageId ? packageId.id : 0)
            $select.trigger('change')
        },

        /**
         * @returns {Promise<void>}
         * @private
         */
        async _onSave() {
            await this._rpc({
                model: 'stock.move.line',
                method: 'put_in_exists_pack',
                args: [this.actionState.productList.map(el => el.moveLineIntId), this.actionState.packageIntId]
            })
            if (this.actionState.packageIntId) {
                $('.barcode-picking-dialog__print-container').show()
            }
            this.$buttons.first().addClass('w-100')
            this.$buttons.last().remove()
            this.$('[data-event="create_package"]').remove()
            this.$('#package_select').attr('disabled', true)
        },

        _onClose() {
            this.do_action({type: 'ir.actions.act_window_close'})
        },
    })

    action_registry.add('package_barcode_action', PackageBarcodeAction)

});