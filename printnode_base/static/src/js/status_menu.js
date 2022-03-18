odoo.define('printnode.status_menu', function (require) {
    "use strict";

    const ajax = require('web.ajax');
    const SystrayMenu = require('web.SystrayMenu');
    const Widget = require('web.Widget');

    const WORKSTATION_DEVICES = require('printnode_base.constants');

    const ActionMenu = Widget.extend({
        template: 'printnode_status_menu',

        init: function (parent, options) {
            this._super.apply(this, arguments);

            this.limits = [];
            this.releases = [];
            this.newRelease = false;
            this.loaded = false;
        },

        willStart: function () {
            // Rate Us URL
            let odooVersion = odoo.session_info.server_version;
            // This attribute can include some additional symbols we do not need here (like 12.0e+)
            odooVersion = odooVersion.substring(0, 4);
            this.rateUsURL = `https://apps.odoo.com/apps/modules/${odooVersion}/printnode_base/#ratings`;

            const limitsPromise = this._rpc({ model: 'printnode.account', method: 'get_limits' });

            // Check if model with releases already exists 
            const releasesPromise = ajax.post("/dpc/release-model-check").then((data) => {
                const status = JSON.parse(data);

                // If model exists load releases
                if (status) {
                    return this._rpc({ model: 'printnode.release', method: 'search_read' });
                }
                // If not exist return empty array
                return [];
            });

            // Get information about workstation devices
            const devicesInfo = Object.fromEntries(
                WORKSTATION_DEVICES
                    .map(n => [n, localStorage.getItem('printnode_base.' + n)])  // Two elements array
                    .filter(i => i[1]) // Skip empty values
            );

            const devicesPromise = this._rpc({
                model: 'res.users',
                method: 'validate_device_id',
                kwargs: { devices: devicesInfo }
            })

            return Promise.all(
                [limitsPromise, releasesPromise, devicesPromise]
            ).then(this._loadedCallback.bind(this));
        },

        _loadedCallback: function ([limits, releases, devices]) {
            // Process limits
            this.limits = limits;

            // Process accounts
            this.releases = releases;
            this.newRelease = releases.length > 0;

            // Process workstation devices
            this.devices = WORKSTATION_DEVICES.map(
                device => {
                    // Remove printnode_ and _id from the of string
                    let deviceName = device.substring(10, device.length - 3).replaceAll('_', ' ');

                    // Return pairs (type, name)
                    return [this._capitalizeWords(deviceName), devices[device]];
                }
            );

            // Loading ended
            this.loaded = true;
        },

        _capitalizeWords: (str) => {
            const words = str.split(" ");
            let capitalizedWords = words.map(w => w[0].toUpperCase() + w.substr(1))
            return capitalizedWords.join(' ');
        }
    });

    SystrayMenu.Items.push(ActionMenu);

    return ActionMenu;
});
