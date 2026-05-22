# UI Icon Code Dictionary

This document serves as a complete reference of all the custom **inline SVG icons** used in the S-Chat (ChatGPT Clone) frontend interface. These icons are fully vector-based, lightweight, responsive, and styled dynamically via CSS.

---

## 1. Sidebar Icons ([Sidebar.jsx](file:///e:/PROJECTS/f-ai/chatgpt_clone/frontend/src/components/chat/Sidebar.jsx))

| Icon Name                   | Category / Purpose   | Properties                    | Code Snippet                                                                                                                                                                                                                                                                                                 |
| :-------------------------- | :------------------- | :---------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Collapse Sidebar**  | Navigation Control   | `18x18`, Stroke: 2, No Fill | ``xml\n<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <rect x="3" y="3" width="18" height="18" rx="2"/>\n  <line x1="9" y1="3" x2="9" y2="21"/>\n</svg>\n``                                              |
| **New Chat**          | Compose Actions      | `16x16`, Stroke: 2, No Fill | ``xml\n<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <path d="M12 20h9"/>\n  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>\n</svg>\n``                                            |
| **Search Chats**      | Filter History       | `16x16`, Stroke: 2, No Fill | ``xml\n<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <circle cx="11" cy="11" r="8"/>\n  <line x1="21" y1="21" x2="16.65" y2="16.65"/>\n</svg>\n``                                                       |
| **Projects**          | Navigation / Folders | `16x16`, Stroke: 2, No Fill | ``xml\n<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>\n</svg>\n``                                                |
| **Codex**             | Technical / Console  | `16x16`, Stroke: 2, No Fill | ``xml\n<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <polyline points="16 18 22 12 16 6"/>\n  <polyline points="8 6 2 12 8 18"/>\n</svg>\n``                                                            |
| **More**              | Context Menus        | `16x16`, Stroke: 2, No Fill | ``xml\n<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <circle cx="12" cy="12" r="1"/>\n  <circle cx="19" cy="12" r="1"/>\n  <circle cx="5" cy="12" r="1"/>\n</svg>\n``                                   |
| **Sign Out / Logout** | Account Actions      | `14x14`, Stroke: 2, No Fill | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>\n  <polyline points="16 17 21 12 16 7"/>\n  <line x1="21" y1="12" x2="9" y2="12"/>\n</svg>\n`` |

---

## 2. Chat Input Icons ([ChatInput.jsx](file:///e:/PROJECTS/f-ai/chatgpt_clone/frontend/src/components/chat/ChatInput.jsx))

| Icon Name                   | Category / Purpose  | Properties                      | Code Snippet                                                                                                                                                                                                                                                                                                                                                          |
| :-------------------------- | :------------------ | :------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Attach / Plus**     | Form Actions        | `18x18`, Stroke: 2, No Fill   | ``xml\n<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <line x1="12" y1="5" x2="12" y2="19"/>\n  <line x1="5" y1="12" x2="19" y2="12"/>\n</svg>\n``                                                                                                                |
| **Voice Input / Mic** | Alternative Inputs  | `18x18`, Stroke: 2, No Fill   | ``xml\n<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>\n  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>\n  <line x1="12" y1="19" x2="12" y2="23"/>\n  <line x1="8" y1="23" x2="16" y2="23"/>\n</svg>\n`` |
| **Send Message**      | Form submission     | `16x16`, Filled shape         | ``xml\n<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">\n  <path d="M12 4l8 16-8-4-8 4 8-16z"/>\n</svg>\n``                                                                                                                                                                                                                                       |
| **Create Image**      | Suggestion Chip     | `14x14`, Stroke: 2, No Fill   | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <rect x="3" y="3" width="18" height="18" rx="2"/>\n  <circle cx="8.5" cy="8.5" r="1.5"/>\n  <polyline points="21 15 16 10 5 21"/>\n</svg>\n``                                                               |
| **Write/Edit text**   | Suggestion Chip     | `14x14`, Stroke: 2, No Fill   | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <path d="M12 20h9"/>\n  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>\n</svg>\n``                                                                                                     |
| **Look Up Globe**     | Suggestion Chip     | `14x14`, Stroke: 2, No Fill   | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <circle cx="12" cy="12" r="10"/>\n  <line x1="2" y1="12" x2="22" y2="12"/>\n  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>\n</svg>\n``            |
| **Model Dropdown**    | Chevron selector    | `12x12`, Stroke: 2.5, No Fill | ``xml\n<svg className="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">\n  <polyline points="6 9 12 15 18 9"/>\n</svg>\n``                                                                                                                                       |
| **Model Selection**   | Selection Checkmark | `14x14`, Stroke: 2.5, No Fill | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">\n  <polyline points="20 6 9 17 4 12"/>\n</svg>\n``                                                                                                                                                           |

---

## 3. Header Icons ([Header.jsx](file:///e:/PROJECTS/f-ai/chatgpt_clone/frontend/src/components/common/Header.jsx))

| Icon Name                | Category / Purpose | Properties                      | Code Snippet                                                                                                                                                                                                                                                              |
| :----------------------- | :----------------- | :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Header Chevron** | Mode Switcher      | `14x14`, Stroke: 2.5, No Fill | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">\n  <polyline points="6 9 12 15 18 9"/>\n</svg>\n``                                                               |
| **Notifications**  | Alerts / Bell      | `18x18`, Stroke: 1.8, No Fill | ``xml\n<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">\n  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>\n  <path d="M13.73 21a2 2 0 0 1-3.46 0"/>\n</svg>\n`` |

---

## 4. Conversation List Icons ([ConversationList.jsx](file:///e:/PROJECTS/f-ai/chatgpt_clone/frontend/src/components/chat/ConversationList.jsx))

| Icon Name             | Category / Purpose | Properties                    | Code Snippet                                                                                                                                                                                                                                                                                          |
| :-------------------- | :----------------- | :---------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Delete Chat** | History Management | `14x14`, Stroke: 2, No Fill | ``xml\n<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">\n  <polyline points="3 6 5 6 21 6"/>\n  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>\n</svg>\n`` |

---

## Styling Guidelines for Icon Customization

To edit the color or dimensions of these icons in the stylesheet, use these CSS properties:

1. **Changing Size**: Update both the `width` and `height` properties in the CSS, or modify the direct JSX parameters.
2. **Changing Color**:
   * For stroke-only icons (`fill="none" stroke="currentColor"`), customize the parent text `color` value in your CSS block.
   * For filled shape icons (`fill="currentColor"`), customize the parent text `color` value or explicitly override `fill` inside your CSS rules (e.g., `.send-btn.active svg { fill: #000000; }`).
3. **Smooth Transitions**: Combine color shifts with transition properties to mimic premium hardware animations:
   ```css
   .icon-class {
     transition: color 0.15s ease, transform 0.15s ease;
   }
   .icon-class:hover {
     color: var(--text-primary);
     transform: scale(1.05);
   }
   ```
