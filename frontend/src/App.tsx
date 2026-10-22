import { useState } from "react";
import { Layout, Segmented, Typography } from "antd";
import ChildLearning from "@/features/child/pages/ChildLearning";
import ParentDashboard from "@/features/parent/pages/ParentDashboard";

const { Header, Content } = Layout;

export default function App() {
  const [mode, setMode] = useState<"child" | "parent">("child");

  return (
    <Layout
      className={`min-h-screen ${mode === "child" ? "child-app" : "bg-slate-50"}`}
    >
      <Header className="app-header">
        <Typography.Title level={4} className="app-brand">
          拾光学堂
        </Typography.Title>
        <Segmented
          value={mode}
          onChange={(value) => setMode(value as "child" | "parent")}
          options={[
            { label: "孩子学习", value: "child" },
            { label: "家长管理", value: "parent" },
          ]}
        />
      </Header>
      <Content
        className={
          mode === "child" ? "child-content" : "mx-auto w-full max-w-6xl p-6"
        }
      >
        {mode === "child" ? <ChildLearning /> : <ParentDashboard />}
      </Content>
    </Layout>
  );
}
