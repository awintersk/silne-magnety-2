odoo.define('printnode_base.set_worstation_devices', function (require) {
    "use strict";

    /*
    This file includes few snippets related to storing/clearing information about workstation
    printers/scales. A bit 'hacky' thing :)
    */
    const rpc = require('web.rpc');
    const localStorage = require('web.local_storage');

    const WORKSTATION_DEVICES = require('printnode_base.constants');

    let sessionInfo = odoo.session_info;

    // Remove information about workstation printers from localStorage when logout
    const currentUserId = sessionInfo.uid;
    const storageUserId = localStorage.getItem('printnode_base.user_id');

    // If not user found in localStorage or user changed - clean workstation devices
    if (!storageUserId || (currentUserId != parseInt(storageUserId))) {
        for (let workstationDevice of WORKSTATION_DEVICES) {
            localStorage.removeItem('printnode_base.' + workstationDevice);
        }
    }

    // Save current user in localStorage
    localStorage.setItem('printnode_base.user_id', currentUserId);

    // Check if devices with IDs from localStorage exists
    const devicesInfo = Object.fromEntries(
        WORKSTATION_DEVICES
            .map(n => [n, localStorage.getItem('printnode_base.' + n)])  // Two elements array
            .filter(i => i[1]) // Skip empty values
    );

    rpc.query({
        model: 'res.users',
        method: 'validate_device_id',
        kwargs: { devices: devicesInfo }
    }).then((data) => {
        // Remove bad device IDs from localStorage
        for (const workstationDevice in data) {
            if (data[workstationDevice]) {
                // ID is correct, place in session
                let workstationDeviceId = localStorage.getItem(
                    'printnode_base.' + workstationDevice);

                if (workstationDeviceId) {
                    // Add information about printer to user context
                    sessionInfo.user_context[workstationDevice] = workstationDeviceId;
                }
            } else {
                // Remove from localStorage
                localStorage.removeItem('printnode_base.' + workstationDevice);
            }
        }
    });
});
