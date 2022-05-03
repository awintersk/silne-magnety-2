odoo.define('barcode_manager_customization.BarcodeReceiptDialog', function (require) {
    'use strict'

    const {_t} = require('web.core')
    const {Component, useState, mount} = owl
    const {SecondaryBody} = require('barcode_manager_customization.secondary_body')

    /**
     * @typedef {{
     *   dont_show_again: Boolean,
     *   items: Array<BarcodeDialogComponentItem>,
     * }} BarcodeReceiptDialogState
     * /

     /**
     * @extends Component
     */
    class BarcodeReceiptDialog extends Component {
        setup() {
            /**@type{BarcodeReceiptDialogState}*/
            this.state = useState({
                items: Object.assign([], this.props.items),
                dont_show_again: false,
            })
        }

        /**
         * @returns {Number}
         */
        get selectedQty() {
            return this.state.items.reduce((acc, el) => acc + el.qty, 0)
        }

        get parentWidget() {
            return this.__owl__.parent ? this.__owl__.parent.parentWidget : undefined
        }

        /**
         * @param {BarcodeDialogComponentItem} item
         * @returns {Boolean}
         */
        activeValidateButton(item) {
            const {totalQty} = this.props.product
            const isCorrectRange = item.qty > 0 && item.qty <= item.qtyToDeliver
            return isCorrectRange && item.qty <= totalQty && !item.confirmed
        }

        /**
         * @param {BarcodeDialogComponentItem} item
         * @return {Boolean}
         */
        activePrintButton(item) {
            return !!item.confirmed
        }

        /**
         * @param {BarcodeDialogComponentItem} item
         * @private
         * @returns {Promise<void>}
         */
        async _onValidate(item) {
            await mount(SecondaryBody, {
                target: this.el,
                props: {
                    item,
                    product: this.props.product,
                    destinationLocationList: this.props.destinationLocationList,
                    locationDestID: this.props.locationDestID,
                    locationsByBarcode: this.props.locationsByBarcode,
                }
            })
        }

        /**
         * @param {{item:Object, locationDestID:Number}} detail
         * @private
         * @returns Promise<void>
         */
        async _validate({detail}) {
            const {services} = this.env

            services.blockUI()

            try {
                const {confirmed, orderPickingId, packageId} = await this.rpc({
                    model: 'stock.move.line',
                    method: 'split_move_line_for_order',
                    args: [this.props.lineId],
                    kwargs: {
                        qty: detail.item.qty,
                        order_int_id: detail.item.id,
                        package_int_id: detail.item.boxIntId,
                        package_type_int_id: detail.item.packageTypeIntId,
                        location_dest_int_id: detail.locationDestID,
                    }
                })

                const item = this.state.items.find(el => el.id === detail.item.id)

                item.confirmed = confirmed
                item.orderPickingId = orderPickingId
                item.boxIntId = packageId.id

                services.notification.notify({
                    type: 'success',
                    title: this.env._t('Validated'),
                    message: `${_t('Box')}: ${packageId.name}`,
                    sticky: false,
                });
            } catch (error) {
                console.error(error)
                services.notification.notify({
                    type: "danger",
                    title: this.env._t('Error'),
                    message: this.env._t(error),
                    sticky: false,
                });
            } finally {
                services.unblockUI()
            }
        }

        /**
         * @param {BarcodeDialogComponentItem} item
         * @private
         * @returns {Promise<void>}
         */
        async _onPrintLabel(item) {
            this.trigger('do_action', {
                action: {
                    name: 'Box Label (ZPL)',
                    type: 'ir.actions.report',
                    model: 'stock.quant.package',
                    report_type: 'qweb-text',
                    report_name: 'zpl_label_template.zpl_label_box_view',
                    report_file: 'zpl_label_template.zpl_label_box_view',
                    context: {
                        active_ids: [item.boxIntId]
                    }
                }
            })
        }

        /**
         * @public
         */
        closeDialog() {
            this.parentWidget.trigger('receipt-dialog-close')
        }

        /**
         * @private
         */
        _onChangeShowAgain() {
            this.parentWidget.trigger('receipt-dont-show-again', {
                productId: this.props.product.id,
                action: this.state.dont_show_again ? 'add' : 'remove'
            })
        }
    }

    BarcodeReceiptDialog.template = 'barcode_manager_customization.barcode_dialog'
    BarcodeReceiptDialog.defaultProps = {
        product: {},
        items: [],
        lineId: 0,
        destinationLocationList: [],
        locationDestID: 0,
        locationsByBarcode: [],
    }
    BarcodeReceiptDialog.props = {
        product: Object,
        items: Array,
        lineId: Number,
        destinationLocationList: Object,
        locationDestID: Number,
        locationsByBarcode: Object,
    }

    return {BarcodeReceiptDialog}

});