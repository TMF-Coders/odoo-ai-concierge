/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { AiConciergeChat } from "../chat/chat";

export class AiConciergeSystray extends Component {
    static template = "ai_concierge.Systray";
    static components = { AiConciergeChat };

    setup() {
        this.state = useState({ isOpen: false });
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    closeChat() {
        this.state.isOpen = false;
    }
}

// Register the icon in Odoo's top right navigation bar (Systray)
registry.category("systray").add("ai_concierge_systray", {
    Component: AiConciergeSystray,
}, { sequence: 10 });
