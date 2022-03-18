odoo.define('printnode_base.res_users_many2one', function (require) {
    "use strict";

    var FieldMany2One = require('web.relational_fields').FieldMany2One;
    var FieldRegistry = require('web.field_registry');
    var localStorage = require('web.local_storage');

    var WorkstationDeviceField = FieldMany2One.extend({
        start: function () {
            this._super.apply(this, arguments);

            // Update value of workstation
            let workstationDeviceId = localStorage.getItem('printnode_base.' + this.name);

            if (workstationDeviceId) {
                this._setValue(workstationDeviceId);
            }
        },
    });

    FieldRegistry.add('res_users_workstation_device_many2one', WorkstationDeviceField);

    return WorkstationDeviceField;
});
