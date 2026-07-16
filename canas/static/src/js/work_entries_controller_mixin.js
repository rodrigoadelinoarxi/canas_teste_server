odoo.define('your_module.YourWorkEntryPayrollControllerMixin', function (require) {
    'use strict';

    var core = require('web.core');
    var WorkEntryPayrollControllerMixin = require('hr_payroll.WorkEntryPayrollControllerMixin');
    WorkEntryPayrollControllerMixin.updateButtons = function () {
        this._super.apply(this, arguments);

        if (!this.$buttons) {
            return;
        }

        var records = this._fetchRecords();
        var hasConflicts = records.some(function (record) { return record.state === 'conflict'; });
        var allValidated = records.every(function (record) { return record.state === 'validated'; });
        var generateButton = this.$buttons.find('.btn-payslip-generate');

        if (!allValidated && records.length !== 0) {
            generateButton.show();
            generateButton.replaceWith(this._renderGeneratePayslipButton(hasConflicts));
        }
    };

    return WorkEntryPayrollControllerMixin;
});
