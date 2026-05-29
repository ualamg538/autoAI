import { useState } from "react";
import Layout from "./components/Layout";
import ChatAssistant from "./components/ChatAssistant";
import Catalog from "./components/Catalog";
import History from "./components/History";
import Favorites from "./components/Favorites";
import type { ViewKey } from "./components/Sidebar";
import {
  getCurrentSessionId,
  newSessionId,
  setCurrentSessionId,
} from "./lib/storage";

function App() {
  const [activeView, setActiveView] = useState<ViewKey>("assistant");
  const [sessionId, setSessionId] = useState<string>(
    () => getCurrentSessionId() ?? newSessionId(),
  );

  function startNewSession() {
    const id = newSessionId();
    setCurrentSessionId(id);
    setSessionId(id);
    setActiveView("assistant");
  }

  function openSession(id: string) {
    setCurrentSessionId(id);
    setSessionId(id);
    setActiveView("assistant");
  }

  return (
    <Layout activeView={activeView} onSelectView={setActiveView}>
      {activeView === "assistant" && (
        <ChatAssistant
          key={sessionId}
          sessionId={sessionId}
          onNewSession={startNewSession}
        />
      )}
      {activeView === "catalog" && <Catalog />}
      {activeView === "history" && <History onOpenSession={openSession} />}
      {activeView === "favorites" && <Favorites />}
    </Layout>
  );
}

export default App;
