odoo.define('barcode_remember.remember_lang_warning_dialog', function (require) {
    'use strict'

    const patchMixin = require('web.patchMixin')
    const Dialog = require('web.OwlDialog')
    const {Component, tags, useState} = owl

    /**
     * @typedef {Object} RememberLanguageWarningDialogState
     * @property {Object} country
     */

    /**
     * @property {RememberLanguageWarningDialogState} state
     * @property {{pickingID: Number}} props
     */
    class RememberLanguageWarningDialog extends Component {
        setup() {
            this.state = useState({
                country: {},
                language: {},
            })
        }

        async willStart() {
            const response = await this.rpc({
                route: '/barcode_remember/warning/country', params: {
                    picking: this.props.pickingID
                }
            })
            Object.assign(this.state, {
                language: response.language,
                country: response.country,
            })
        }

        _onCloseDialog() {
            this.destroy()
        }

        _onValidate() {
            this.trigger('validate')
            this.destroy()
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
                 class="o_barcode_icon"
                 alt="Barcode"
                 height="70"
                 style="object-fit: contain;"/>
             <br/>
            <span class="d-flex flex-column justify-content-center">
                <span>
                    <i class="fa fa-map"/>
                    <b class="pl-2">Country</b>: <t t-esc="state.country.name"/>
                </span>
                <span>
                    <i class="fa fa-language"/> 
                    <b class="pl-2">Language</b>: <t t-esc="state.language.name"/>
                </span>
            </span>
        </div>
        <t t-set-slot="buttons">
            <button class="btn btn-primary w-100" t-on-click="_onValidate">Validate</button>
        </t>
    </Dialog>
    `

    return {LanguageWarningDialog: patchMixin(RememberLanguageWarningDialog)}
});