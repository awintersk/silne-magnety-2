odoo.define('zpl_label_template.utils', function (require) {
    'use strict'

    const rpc = require('web.rpc')

    const {Component} = owl
    const {onMounted, onWillUnmount} = owl.hooks

    /**
     * @param {Number} [productId]
     * @param {String} [barcode]
     * @return {Promise<Number>}
     */
    async function getProductZPLReportId({productId, barcode}) {
        return await rpc.query({
            route: '/zpl_label_template/get_product_zpl_report_id',
            params: {
                product_int_id: productId,
                barcode: barcode,
            }
        })
    }

    /**
     * @param {TimerHandler} handler
     * @param {Number} [timeout]
     * @return {Number|null}
     */
    function useInterval({handler, timeout}) {
        let intervalId = null

        onMounted(() => {
            intervalId = setInterval(handler.bind(Component.current), timeout)
        })
        onWillUnmount(() => {
            clearInterval(intervalId)
        })

        return intervalId
    }

    return {getProductZPLReportId, useInterval}
});