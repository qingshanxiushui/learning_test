import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import App from "./App";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#24665c",
          colorInfo: "#24665c",
          colorSuccess: "#318452",
          colorWarning: "#e0a838",
          colorError: "#d96a43",
          colorText: "#1c3134",
          colorTextSecondary: "#4a463f",
          colorTextTertiary: "#857e74",
          colorBorder: "#ede7dc",
          colorBorderSecondary: "#f2ece1",
          colorBgLayout: "#faf6ee",
          colorBgContainer: "#ffffff",
          borderRadius: 12,
          borderRadiusLG: 20,
          controlHeight: 38,
          fontSize: 14,
          fontFamily:
            '"PingFang SC", "HarmonyOS Sans", "Microsoft YaHei", "Noto Sans SC", sans-serif',
          boxShadowSecondary:
            "0 8px 24px -4px rgba(28,49,52,0.06), 0 2px 6px -1px rgba(28,49,52,0.04)"
        },
        components: {
          Layout: {
            headerBg: "transparent",
            bodyBg: "transparent",
            headerPadding: 0
          },
          Card: {
            borderRadiusLG: 20,
            paddingLG: 22
          },
          Button: {
            borderRadius: 12,
            borderRadiusLG: 16,
            fontWeight: 600,
            primaryShadow: "0 6px 16px rgba(36,102,92,0.28)"
          },
          Segmented: {
            itemSelectedBg: "#ffffff",
            itemSelectedColor: "#004e45",
            trackBg: "rgba(237,231,220,0.85)",
            borderRadius: 999
          },
          Table: {
            headerBg: "#f5efe6",
            headerColor: "#4a463f",
            headerSplitColor: "transparent",
            rowHoverBg: "#fdfbf7",
            borderColor: "#ede7dc",
            cellPaddingBlock: 14,
            borderRadiusLG: 16
          },
          Tabs: {
            itemSelectedColor: "#004e45",
            itemHoverColor: "#24665c",
            inkBarColor: "#24665c",
            titleFontSize: 15
          },
          Modal: {
            borderRadiusLG: 24,
            paddingContentHorizontalLG: 28
          },
          Input: {
            borderRadius: 12,
            activeBorderColor: "#24665c",
            hoverBorderColor: "#a9c4bf",
            activeShadow: "0 0 0 3px rgba(36,102,92,0.1)"
          },
          InputNumber: {
            borderRadius: 12,
            activeBorderColor: "#24665c",
            hoverBorderColor: "#a9c4bf",
            activeShadow: "0 0 0 3px rgba(36,102,92,0.1)"
          },
          Select: {
            borderRadius: 12,
            optionSelectedBg: "#f2f7f6",
            optionSelectedColor: "#004e45"
          },
          Progress: {
            defaultColor: "#24665c"
          },
          Tag: {
            borderRadiusSM: 999
          },
          Switch: {
            colorPrimary: "#24665c"
          },
          Statistic: {
            contentFontSize: 30
          }
        }
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
