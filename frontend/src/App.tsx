import { useState } from "react";
import Layout from "./components/Layout";
import ChatAssistant from "./components/ChatAssistant";
import type { ViewKey } from "./components/Sidebar";

function StubView({ title }: { title: string }) {
  return (
    <div className="stub-view">
      <div>
        <strong>{title}</strong> — próximamente
      </div>
    </div>
  );
}

function App() {
  const [activeView, setActiveView] = useState<ViewKey>("assistant");

  return (
    <Layout activeView={activeView} onSelectView={setActiveView}>
      {activeView === "assistant" && <ChatAssistant />}
      {activeView === "catalog" && <StubView title="Catálogo" />}
      {activeView === "history" && <StubView title="Historial" />}
      {activeView === "favorites" && <StubView title="Favoritos" />}
    </Layout>
  );
}

export default App;
