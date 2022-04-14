odoo.define('barcode_manager_customization.backend_main', function (require) {
    'use strict'

    const PickingClientAction = require('stock_barcode.picking_client_action')
    const Dialog = require('web.Dialog')
    const config = require('web.config');
    const {BarcodeReceiptDialog} = require('barcode_manager_customization.BarcodeReceiptDialog')
    const {BarcodeInternalDialog} = require('barcode_manager_customization.BarcodeInternalDialog')
    const {BarcodeEvents} = require('barcodes.BarcodeEvents')
    const {bus, _t} = require('web.core')
    const {ComponentWrapper} = require('web.OwlCompatibility')

    const session = require('web.session');

    /**
     * @typedef {{
     * id: Number,
     * name: String,
     * partnerName: String,
     * qtyToDeliver: Number,
     * [qty]: Number,
     * [confirmed]: Boolean,
     * [orderPickingId]: Number,
     * [boxIntId]: Number,
     * }} BarcodeDialogComponentItem
     */

    /**
     * @typedef {Boolean} session.use_barcode_keypress_event
     */

    PickingClientAction.include({
        barcodeScannerActive: true,

        custom_events: Object.assign({},
            PickingClientAction.prototype.custom_events,
            {
                'receipt-dialog-close': '_onCloseOrderNTDialog',
                'receipt-dont-show-again': '_onDontShowNTDialog',
                'default-barcode-scanner': '_onDefaultBarcodeScanner',
            }
        ),

        init() {
            this._super.apply(this, arguments)
            this.ntOrderDialog = undefined
            this.dontShowOrderPopup = []
            this.initBarcodeScannerEmulator()
        },

        initBarcodeScannerEmulator() {
            if (window.barcodeScanner) return;
            if (odoo.debug !== '1') return;

            window.barcodeScanner = {
                /**@param {String} decodedBarcode*/
                scan(decodedBarcode) {
                    bus.trigger('barcode_scanned', decodedBarcode)
                }
            }
        },

        /**
         * @param {String} name
         * @returns {Promise<*>}
         */
        getParam(name) {
            return this._rpc({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: [name],
            })
        },

        /**
         * @param {String} barcode
         * @returns {Promise<{id: Number, quant_ids: Array[]}>}
         * @private
         */
        async _fetchPackage(barcode) {
            const [response] = await this._rpc({
                model: 'stock.quant.package',
                method: 'search_read',
                domain: [['name', '=', barcode]],
                fields: ['id'],
                limit: 1,
            })
            return response
        },

        /**
         * @override
         * @return {Boolean}
         * @private
         */
        _isAbleToCreateNewLine() {
            return true;
        },

        _onDefaultBarcodeScanner({active}) {
            this.barcodeScannerActive = active
        },

        /**
         * @param {String} barcode
         * @returns {Promise<*>}
         * @private
         */
        async _onBarcodeScanned(barcode) {
            if (!this.barcodeScannerActive) {
                return Promise.resolve();
            }

            const _super = this._super
            const isProductBarcode = Boolean(this.productsByBarcode[barcode])
            /**@type{String}*/
            const seqCode = this.initialState.picking_sequence_code

            switch (seqCode) {
                case 'IN':
                    if (isProductBarcode && await this._onBarcodeScannedReceipt(barcode)) return Promise.resolve();
                    break;
                case 'PICK':
                    if (isProductBarcode && await this._onBarcodeScannedInternal(barcode)) return Promise.resolve();
                    break;
                case 'OUT':
                    if (!isProductBarcode && await this._onBarcodeScannedDelivery(barcode)) return Promise.resolve();
                    break;
            }

            return _super.apply(this, arguments)
        },

        /**
         * @param {String} barcode
         * @return {Promise<boolean>}
         * @private
         */
        async _onBarcodeScannedReceipt(barcode) {
            const product = this.productsByBarcode[barcode]

            const [lineId] = await this._rpc({
                model: 'stock.move.line',
                method: 'search_read',
                domain: [['picking_id', '=', this.currentState.id], ['product_id', '=', product.id]],
                fields: ['display_name', 'product_id', 'product_uom_id', 'product_uom_qty', 'qty_done'],
                limit: 1
            })

            if (!lineId) {
                this.displayNotification({title: 'There are no lines to process'})
                return true
            }

            product.totalQty = lineId.product_uom_qty
            product.display_name = lineId.display_name

            if (this.dontShowOrderPopup.includes(product.id)) {
                return false
            }

            /**@type{Array<BarcodeDialogComponentItem>}*/
            let items = await this._rpc({
                route: '/product_order_dialog_data',
                params: {
                    product_int_id: product.id,
                    line_id: lineId.id,
                }
            })

            if (items.length) {
                await this._openNtOrderDialog(items, product, lineId.id)
                return true
            }

            this.dontShowOrderPopup.push(product.id)

            return false
        },

        /**
         * @param {String} barcode
         * @return {Promise<boolean>}
         * @private
         */
        async _onBarcodeScannedInternal(barcode) {
            if (!await this.getParam('barcode_manager_customization.use_barcode_picking_dialog')) {
                return false
            }

            const moveLineIds = this.currentState.move_line_ids

            /**@type{Object<*>|undefined}*/
            const linesId = moveLineIds.find(rec => {
                const getID = rec => rec ? rec[0] : null
                if (rec.product_barcode !== barcode) return false;
                if (rec.qty_done >= rec.product_uom_qty) return false
                return !rec.result_package_id || getID(rec.package_id) === getID(rec.result_package_id)
            })

            if (!linesId) {
                this.displayNotification({
                    type: 'danger',
                    title: 'Barcode',
                    message: `Product Barcode: <strong>${barcode}</strong> is not found.`
                })
                return true
            }

            await this._save()

            const internalBody = new ComponentWrapper(this, BarcodeInternalDialog, {
                linesId,
                moveLineIds,
                pickingIntId: this.currentState.id,
            })

            await internalBody.mount(this.el)

            return true
        },

        /**
         * @param {String} barcode
         * @return {Promise<boolean>}
         * @private
         */
        async _onBarcodeScannedDelivery(barcode) {
            const packageId = await this._fetchPackage(barcode)

            if (!packageId) {
                this.displayNotification({
                    type: 'danger',
                    title: 'Barcode',
                    message: `Package Barcode: <strong>${barcode}</strong> is not found.`
                })
                return true
            }

            await this._save()

            this.barcodeScannerActive = false

            this.do_action({
                    type: 'ir.actions.client',
                    tag: 'package_barcode_action',
                    name: barcode,
                    target: 'new',
                    context: {
                        pickingId: {id: this.currentState.id},
                        packageId: packageId,
                        barcode: barcode,
                        mode: this.mode
                    }
                },
                {
                    fullscreen: config.device.isMobile,
                    on_close: () => {
                        this.barcodeScannerActive = true
                        this.trigger_up('reload')
                    }
                })

            return true
        },

        /**
         * @param event
         * @param {Number} event.data.id
         * @param {Number} [event.data.qty]
         * @param {*} event.target
         * @returns {Promise<void>}
         * @private
         */
        async _onIncrementLine(event) {
            const lineIntId = event.data.id
            const _super = this._super

            let lineId = this.currentState.move_line_ids.filter(el => el.id === lineIntId)

            if (!lineId.length) {
                return;
            } else {
                lineId = lineId[0]
            }

            const product = Object.assign({}, lineId.product_id)

            product.totalQty = lineId.product_uom_qty
            product.display_name = lineId.display_name

            if (this.dontShowOrderPopup.includes(product.id) && event.target.mode === 'receipt') {
                _super.apply(this, arguments)
            } else if (this.mode === 'receipt') {
                /**@type{Array<BarcodeDialogComponentItem>}*/
                let items = await this._rpc({
                    route: '/product_order_dialog_data',
                    params: {
                        product_int_id: product.id,
                        line_id: lineId.id
                    }
                })

                if (items.length) {
                    await this._openNtOrderDialog(items, product, lineId.id)
                } else {
                    this.dontShowOrderPopup.push(product.id)
                    _super.apply(this, arguments)
                }
            } else {
                _super.apply(this, arguments)
            }
        },

        /**
         * @private
         */
        _onCloseOrderNTDialog() {
            if (this.ntOrderDialog) {
                this.ntOrderDialog.close()
            }
        },

        /**
         * @param event
         * @param {Number} event.productId
         * @param {String} event.action
         * @private
         */
        _onDontShowNTDialog(event) {
            switch (event.action) {
                case 'add':
                    this.dontShowOrderPopup.push(event.productId)
                    break;
                case 'remove':
                    this.dontShowOrderPopup = this.dontShowOrderPopup.filter(el => el !== event.productId)
                    break;
            }
        },

        /**
         * @param {Object<*>} product
         * @param {Array<*>} items
         * @param {Number} lineId
         * @returns {Promise<void>}
         * @private
         */
        async _openNtOrderDialog(items, product, lineId) {
            if (this.ntOrderDialog) {
                this.ntOrderDialog.close()
            }

            const content = document.createElement('div')
            /**@type{BarcodeReceiptDialog|Component|ComponentWrapper}*/
            const ntOrderDialogComponent = new ComponentWrapper(this, BarcodeReceiptDialog, {
                product,
                items: items.map(item => Object.assign({}, item, {
                    boxIntId: 0,
                    confirmed: false,
                })),
                lineId,
            })
            await ntOrderDialogComponent.mount(content)

            this.ntOrderDialog = new Dialog(this, {
                renderFooter: false,
                technical: false,
                fullscreen: true,
                $content: $(content),
                title: product.display_name,
                onForceClose: () => {
                    this.trigger_up('reload')
                    ntOrderDialogComponent.destroy()
                    this.barcodeScannerActive = true
                },
            })

            this.ntOrderDialog._opened.then(() => {
                this.barcodeScannerActive = false
            })

            this.ntOrderDialog.open({shouldFocusButtons: false})
        },
    })

    const oldListenBarcodeScanner = BarcodeEvents.__proto__._listenBarcodeScanner

    BarcodeEvents._listenBarcodeScanner = function (event) {
        if (session.use_barcode_keypress_event) {
            $('body').bind("keypress", this.__handler);
        } else {
            /**@type{HTMLElement}*/
            const activeElement = document.activeElement
            const isDialog = activeElement.getAttribute('role') === 'dialog'

            if (isDialog) {
                $(activeElement).append(this.$barcodeInput);
                this.$barcodeInput.focus();
            }
            oldListenBarcodeScanner.apply(this, [event])
        }
    }

    return {}
});