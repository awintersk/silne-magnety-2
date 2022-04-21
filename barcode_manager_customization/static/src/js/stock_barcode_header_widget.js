odoo.define('barcode_manager_customization.stock_barcode_header_widget', function (require) {
    'use strict'

    const HeaderWidget = require('stock_barcode.HeaderWidget')
    const ClientAction = require('stock_barcode.ClientAction')
    const core = require('web.core')

    HeaderWidget.include({
        events: Object.assign({}, HeaderWidget.prototype.events, {
            'change .nt-move-line-header__search-input': '_onSearchLine',
            'input .nt-move-line-header__search-input': _.debounce(function (event) {
                this._onSearchLine(event)
            }, 200),
        }),

        orderCount: 0,

        async start() {
            const response = await this._super.apply(this, arguments)
            core.bus.on('nt_move_line.updateOrderCounter', this, this._onUpdateOrderCounter)
            return response
        },

        async _onUpdateOrderCounter(event) {
            const picking = await this._rpc({
                model: 'stock.picking',
                method: 'search_read',
                args: [[['id', '=', event.pickingId]]],
                fields: ['barcode_sale_order_ids']
            })

            this.orderCount = picking.length ? picking[0].barcode_sale_order_ids.length : 0
            this.renderElement()
        },

        /**
         * @param {Event} event
         * @private
         */
        _onSearchLine(event) {
            /**@type{HTMLElement}*/
            const ntHeader = event.currentTarget.closest('.nt-move-line-header ')
            core.bus.trigger('nt_move_line.search_line', {search: ntHeader.querySelector('input').value})
        },

    })

    ClientAction.include({
        async start() {
            await this._super.apply(this, arguments)
            core.bus.on('nt_move_line.search_line', this, this._onSearchLine)
            return Promise.resolve()
        },

        /**
         * @param {String} event
         * @private
         */
        _onSearchLine(event) {
            if (this.actionParams.model !== 'stock.picking') return;

            /**@type{jQuery}*/
            const $lines = this.$el.find(`.o_barcode_line[data-id]`)

            if (event.search) {
                /**@type{Array<Number>}*/
                const visibleRecordsIds = this.currentState.move_line_ids.map(el => el.id)

                $lines.removeClass('d-flex').addClass('d-none')

                for (let line of $lines) {
                    if (!visibleRecordsIds.includes(+line.dataset.id)) continue;
                    $(line).addClass('d-flex').removeClass('d-none')
                }

            } else {
                $lines.addClass('d-flex').removeClass('d-none')
            }
        },

        /**
         * @private
         * @param {Object} pageIndex page index
         * @returns {Promise}
         */
        _reloadLineWidget(pageIndex) {
            this.$el.find('.nt-move-line-header__search-input').val('')
            const response = this._super.apply(this, arguments)
            core.bus.trigger('nt_move_line.updateOrderCounter', {
                pickingId: this.currentState.id
            })
            return response
        },
    })
});