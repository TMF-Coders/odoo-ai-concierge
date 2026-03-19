/** @odoo-module **/

import { Component, useState, useRef, onPatched, markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { A2UISurface } from "./a2ui_surface";

export class AiConciergeChat extends Component {
    static template = "ai_concierge.Chat";
    static components = { A2UISurface };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.messageAreaRef = useRef("messageArea");
        this.fileInput = useRef("fileInput");
        this.state = useState({
            messages: [
                {
                    role: 'ai',
                    content: markup('¡Hola! Soy tu <b>AI Concierge</b>. ¿En qué puedo ayudarte en Odoo hoy?'),
                    type: 'text'
                }
            ],
            attachments: [],
            inputText: "",
            isLoading: false,
            isListening: false
        });

        onPatched(() => {
            this.scrollToBottom();
        });

        // Handle card clicks via global event listener (since cards are injected as raw HTML)
        window.addEventListener('open-record', (ev) => {
            const { model, id } = ev.detail;
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: model,
                res_id: id,
                views: [[false, 'form']],
                target: 'current',
            });
        });
    }

    scrollToBottom() {
        if (this.messageAreaRef.el) {
            this.messageAreaRef.el.scrollTop = this.messageAreaRef.el.scrollHeight;
        }
    }

    renderMarkdown(text) {
        if (!text) return "";
        let html = String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        // Italic
        html = html.replace(/\*(.*?)\*/g, '<i>$1</i>');
        // Lists
        html = html.replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/g, '<ul class="ps-3 mb-2">$1</ul>');
        html = html.replace(/<\/ul>\s*<ul class="ps-3 mb-2">/g, '');
        // Code
        html = html.replace(/`(.*?)`/g, '<code class="bg-light px-1 rounded">$1</code>');
        // Br
        html = html.replace(/\n/g, '<br/>');

        // Cards
        html = html.replace(/\[card:([a-z.]+):(\d+)\]/g, (match, model, id) => {
            return `<div class="ai-entity-card d-flex align-items-center p-2 mt-2 bg-light rounded border shadow-sm" style="cursor: pointer;" onclick="const ev = new CustomEvent('open-record', { detail: { model: '${model}', id: ${id} } }); window.dispatchEvent(ev);">
                <img src="/web/image/${model}/${id}/image_128" class="rounded me-2" style="width: 48px; height: 48px; object-fit: cover; background: #eee;"/>
                <div class="flex-grow-1 overflow-hidden">
                    <div class="fw-bold text-truncate small">${model} #${id}</div>
                    <div class="text-muted" style="font-size: 0.7rem;">Haga clic para abrir ficha</div>
                </div>
                <i class="fa fa-chevron-right text-muted ms-2"/>
            </div>`;
        });

        return markup(html);
    }

    startDictation() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.state.messages.push({
                role: 'ai',
                content: 'Lo siento, el dictado por voz no es compatible con este navegador.',
                type: 'error'
            });
            return;
        }

        if (this.state.isListening) {
            if (this.recognition) this.recognition.stop();
            this.state.isListening = false;
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'es-ES';
        this.recognition.interimResults = true;
        this.recognition.continuous = false;

        this.recognition.onstart = () => {
            this.state.isListening = true;
        };

        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');
            this.state.inputText = transcript;
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            this.state.isListening = false;
        };

        this.recognition.onend = () => {
            this.state.isListening = false;
        };

        this.recognition.start();
    }

    triggerFileInput() {
        this.fileInput.el.click();
    }

    async onFileChange(ev) {
        const files = ev.target.files;
        for (const file of files) {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.state.attachments.push({
                    id: Date.now() + Math.random(),
                    name: file.name,
                    type: file.type,
                    data: e.target.result.split(',')[1], // base64
                    preview: e.target.result,
                });
            };
            reader.readAsDataURL(file);
        }
        // Reset input
        ev.target.value = "";
    }

    removeAttachment(id) {
        this.state.attachments = this.state.attachments.filter(a => a.id !== id);
    }

    async sendMessage() {
        const text = this.state.inputText.trim();
        const attachments = [...this.state.attachments];
        if (!text && attachments.length === 0 || this.state.isLoading) return;

        // Add user message to UI
        const userMsg = {
            role: "user",
            content: text,
            attachments: attachments.map(a => ({ name: a.name, type: a.type, preview: a.preview }))
        };
        this.state.messages.push(userMsg);
        this.state.inputText = "";
        this.state.attachments = []; // Clear attachments
        this.state.isLoading = true;
        this.scrollToBottom();

        try {
            // Filter and map previous messages for ADK/Gemini compatibility (roles: user/model)
            const adkHistory = this.state.messages
                .slice(0, -1) // Exclude the new message we just pushed, as it's passed as main arg
                .filter(m => m.type !== 'action_feedback' && m.type !== 'error')
                .map(m => ({
                    role: m.role === 'ai' ? 'model' : 'user',
                    parts: [{ text: String(m.content) }]
                }));

            // Extract visual context from the current active Odoo view
            let activeContext = null;
            const controller = this.action.currentController;
            if (controller && controller.action) {
                activeContext = {
                    active_model: controller.action.res_model || controller.props?.resModel,
                    active_id: controller.action.res_id || controller.props?.resId || controller.state?.resId || (controller.action.context && controller.action.context.active_id),
                    view_type: controller.view && controller.view.type
                };
            }

            // Call the python model method bridging to Google ADK via ORM service, passing history as kwarg
            const response = await this.orm.call(
                "ai.concierge.orchestrator",
                "process_chat_message",
                [userMsg],
                { history: adkHistory, active_context: activeContext }
            );

            if (response.type === 'action' && response.action_xml_id) {
                this.state.messages.push({
                    role: 'ai',
                    content: markup("<i>Navegando a la vista solicitada...</i>"),
                    type: 'action_feedback'
                });
                // Execute Odoo UI Action magically told by the AI Tool!
                try {
                    await this.action.doAction(response.action_xml_id);
                } catch (actionError) {
                    this.state.messages.push({
                        role: 'ai',
                        content: markup(`<span class="text-danger small"><i class="fa fa-exclamation-triangle me-1"/> Error al abrir la vista: <b>${response.action_xml_id}</b>. Asegúrate de que el módulo necesario esté instalado.</span>`),
                        type: 'error'
                    });
                }
            }

            if (response.message) {
                // Check if message contains A2UI payload
                let a2ui_surface = null;
                const a2uiMatch = response.message.match(/\[A2UI_BEGIN\]([\s\S]*?)\[A2UI_END\]/);
                if (a2uiMatch) {
                    try {
                        a2ui_surface = JSON.parse(a2uiMatch[1].trim());
                    } catch (e) {
                        console.error("Invalid A2UI JSON", e);
                    }
                }

                const cleanMessage = response.message.replace(/\[A2UI_BEGIN\][\s\S]*?\[A2UI_END\]/, '').trim();
                this.state.messages.push({
                    role: 'ai',
                    content: this.renderMarkdown(cleanMessage),
                    type: response.type,
                    a2ui_surface: a2ui_surface
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
