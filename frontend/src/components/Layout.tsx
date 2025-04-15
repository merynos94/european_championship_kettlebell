import React, { useState } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Drawer } from "antd";
import { MenuOutlined } from "@ant-design/icons";
import styles from "./Layout.module.css";

const { Header, Content, Footer } = AntLayout;

const Layout: React.FC = () => {
  const location = useLocation();
  const currentYear = new Date().getFullYear();
  const [drawerVisible, setDrawerVisible] = useState(false);

  const showDrawer = () => {
    setDrawerVisible(true);
  };

  const closeDrawer = () => {
    setDrawerVisible(false);
  };

  const getSelectedKeys = () => {
    if (location.pathname.startsWith("/live")) return ["live"];
    if (location.pathname.startsWith("/contact")) return ["contact"];
    return [];
  };

  const menuItems = [
    {
      key: "live",
      label: (
        <Link to="/live" onClick={closeDrawer}>
          Transmisja Live
        </Link>
      ),
    },
    {
      key: "contact",
      label: (
        <Link to="/contact" onClick={closeDrawer}>
          Kontakt
        </Link>
      ),
    },
  ];

  return (
    <AntLayout className={styles.appContainer} style={{ minHeight: "100vh" }}>
      <Header className={styles.header}>
        <div className={styles.logoContainer}>
          <Link to="/" className={styles.logoLink}>
            Hardstyle Kettlebell European Championship - Live Results
          </Link>
        </div>

        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={getSelectedKeys()}
          className={`${styles.navigationMenu} ${styles.desktopNav}`}
          items={menuItems}
          style={{ borderBottom: "none", lineHeight: "inherit" }}
          overflowedIndicator={null}
        />

        <Button
          className={styles.mobileNavButton}
          type="primary"
          icon={<MenuOutlined />}
          onClick={showDrawer}
          ghost
        />

        <Drawer
          title="Menu"
          placement="right"
          onClose={closeDrawer}
          open={drawerVisible}
          styles={{ body: { padding: 0 } }}  // Updated from bodyStyle
          className={styles.mobileDrawer}
        >
        <Menu
          theme="light"
          mode="vertical"
          selectedKeys={getSelectedKeys()}
          items={menuItems}
        />
        </Drawer>
      </Header>

      <Content className={styles.mainContent}>
        <Outlet />
      </Content>
      <Footer className={styles.footer}>
        © {currentYear} Hardstyle Kettlebell European Championship. All rights reserved.
      </Footer>
    </AntLayout>
  );
};

export default Layout;
