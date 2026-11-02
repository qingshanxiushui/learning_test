import { useState } from "react";
import { Layout, Segmented, Typography } from "antd";
import ChildLearning from "@/features/child/pages/ChildLearning";
import ParentDashboard from "@/features/parent/pages/ParentDashboard";

const { Header, Content } = Layout;

export default function App() {
  const [mode, setMode] = useState<"child" | "parent">("child");

  return (
    <Layout className="min-h-screen bg-transparent">
      <Header className="app-header">
        <div className="app-brand">
          <span className="app-brand-mark" aria-hidden="true">
            拾
          </span>
          <div className="app-brand-text">
            <Typography.Title level={4} className="app-brand-title">
              拾光学堂
            </Typography.Title>
            <span className="app-brand-sub">每日拾光 · 快乐积跬步</span>
          </div>
        </div>
        <Segmented
          className="app-mode-switch"
          value={mode}
          onChange={(value) => setMode(value as "child" | "parent")}
          options={[
            { label: "孩子学习", value: "child" },
            { label: "家长管理", value: "parent" },
          ]}
        />
      </Header>
      <Content className={mode === "child" ? "child-content" : "parent-shell"}>
        {mode === "child" ? <ChildLearning /> : <ParentDashboard />}
      </Content>
    </Layout>
  );
}
