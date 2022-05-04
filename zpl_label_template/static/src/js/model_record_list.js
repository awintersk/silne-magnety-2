odoo.define('zpl_template.zpl_view', function (require) {
    'use strict'

    const {_lt} = require('web.core')
    const AbstractFieldOwl = require('web.AbstractFieldOwl')
    const field_registry_owl = require('web.field_registry_owl')
    const {useInterval} = require('zpl_label_template.utils')
    const {useState} = owl

    class ModelRecordList extends AbstractFieldOwl {
        setup() {
            this.state = useState({items: []})
            useInterval({
                handler: this._modelChangeListener,
                timeout: 100
            })
        }

        async willStart() {
            this.state.items = await this._loadRecords()
        }

        get textValue() {
            const valueItem = this.state.items.find(item => item.id === this.value)
            return valueItem ? valueItem.display_name || valueItem.name : ''
        }

        get parentWidget() {
            return this.__owl__.parent.parentWidget
        }

        /**
         * @param [model_id]
         * @return {Promise<*|*[]>}
         * @private
         */
        async _loadRecords(model_id) {
            const {record_limit} = this.nodeOptions

            if (!model_id) {
                model_id = this.recordData.model_id
            }

            if (!model_id) {
                return []
            }

            return await this.rpc({
                route: `/zpl_label_template/record_list/${model_id.res_id}`,
                params: {limit: record_limit}
            })
        }

        _onChangeItem(event) {
            this._setValue(event.target.value)
        }

        async _recordRefresh() {
            const model_id = this.parentWidget.state.data.model_id
            this.state.items = await this._loadRecords(model_id)
            if (this.state.items.length) {
                this._setValue(this._formatValue(this.state.items[0].id))
            }
        }

        async _modelChangeListener() {
            if (this.mode !== 'edit') return;
            if (!this.parentWidget) return;

            const currentModelId = this.recordData.model_id
            const actualModelId = this.parentWidget.state.data.model_id

            if (!actualModelId) return;

            if (!currentModelId || currentModelId.data.id !== actualModelId.data.id) {
                this.recordData.model_id = JSON.parse(JSON.stringify(actualModelId))
                await this._recordRefresh()
            }
        }
    }

    ModelRecordList.template = 'ModelRecordList'
    ModelRecordList.description = _lt('Model Record List')
    ModelRecordList.supportedFieldTypes = ['integer']
    ModelRecordList.fieldDependencies = {
        model_id: {type: 'many2one', relation: 'ir.model'},
    }

    field_registry_owl.add('model_record_list', ModelRecordList)

    return {ModelRecordList}

});