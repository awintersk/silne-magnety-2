odoo.define('printnode_base.ResUsersView', function (require) {
    "use strict";

    const FormController = require('web.FormController');
    const FormView = require('web.FormView');
    const viewRegistry = require('web.view_registry');
    const localStorage = require('web.local_storage');

    const WORKSTATION_DEVICES = require('printnode_base.constants');

    const ResUsersPreferencesFormController = FormController.extend({
        _onButtonClicked: function (event) {
            this._super.apply(this, arguments);

            const attrs = event.data.attrs;
            var sessionInfo = odoo.session_info;

            if (attrs.name === 'preference_save') {
                // Update local printer
                const record = event.data.record;

                for (let workstationDeviceAttr of WORKSTATION_DEVICES) {
                    const workstationDeviceField = record.data[workstationDeviceAttr];

                    if (workstationDeviceField) {
                        const workstationDeviceId = workstationDeviceField.data.id;

                        // Save in localStorage for future use
                        localStorage.setItem('printnode_base.' + workstationDeviceAttr, workstationDeviceId);

                        // Update context to send with every request
                        sessionInfo.user_context[workstationDeviceAttr] = workstationDeviceId;

                    } else {
                        // Clean localStorage
                        localStorage.removeItem('printnode_base.' + workstationDeviceAttr);

                        // Remove from user context
                        delete sessionInfo.user_context[workstationDeviceAttr];
                    }
                }
            }

        }
    });

    const ResUsersPreferencesView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: ResUsersPreferencesFormController,
        }),
    });

    viewRegistry.add('res_users_form', ResUsersPreferencesView);

    return ResUsersPreferencesView;
});
