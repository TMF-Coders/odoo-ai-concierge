/** @odoo-module **/

import { Component, xml } from "@odoo/owl";

export class A2UISurface extends Component {
    static template = "ai_concierge.A2UISurface";
    static props = {
        surface: { type: Object },
    };

    setup() {
        // A2UI Surface structure: { components: [...], dataModel: {...}, root: "id" }
    }

    get components() {
        const componentsMap = {};
        (this.props.surface.components || []).forEach(c => {
            componentsMap[c.id] = c.component;
        });
        return componentsMap;
    }

    get dataModel() {
        return this.props.surface.dataModel || {};
    }

    get rootComponentId() {
        return this.props.surface.root || (this.props.surface.components && this.props.surface.components[0] && this.props.surface.components[0].id);
    }

    resolveValue(binding) {
        if (!binding) return "";
        if (typeof binding === 'object' && binding.boundValue) {
            const val = this.dataModel[binding.boundValue];
            if (val === undefined) {
                console.warn(`[A2UI] Missing binding for: ${binding.boundValue}`);
                return "";
            }
            return val;
        }
        return String(binding);
    }
}
