/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AiConciergeChat extends Component {
    static template = "ai_concierge.Chat";

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({
            messages: [
                { role: 'ai', content: '¡Hola! Soy tu AI Concierge. ¿En qué puedo ayudarte en Odoo hoy?', type: 'text' }
            ],
            inputText: "",
            isLoading: false
        });
    }

    async sendMessage() {
        if (!this.state.inputText.trim() || this.state.isLoading) return;

        const userMsg = this.state.inputText;
        this.state.messages.push({ role: 'user', content: userMsg });
        this.state.inputText = "";
        this.state.isLoading = true;

        try {
            // Call the python controller bridging to Google ADK
            const response = await this.rpc("/ai_concierge/chat", { message: userMsg });

            if (response.type === 'action' && response.action_xml_id) {
                this.state.messages.push({
                    role: 'ai',
                    content: "Navegando a la vista solicitada...",
                    type: 'action_feedback'
                });
                // Execute Odoo UI Action magically told by the AI Tool!
                await this.action.doAction(response.action_xml_id);
            }

            if (response.message) {
                this.state.messages.push({
                    role: 'ai',
                    content: response.message,
                    type: response.type
                });
            }

        } catch (error) {
            this.state.messages.push({
                role: 'ai',
                content: 'Error de conexión con el cerebro de Inteligencia Artificial.',
                type: 'error'
            });
            console.error(error);
        } finally {
            this.state.isLoading = false;
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }
}
