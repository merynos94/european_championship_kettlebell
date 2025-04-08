import React, { PropsWithChildren } from "react";
import { Outlet, Link } from "react-router-dom";
import styles from "./Layout.module.css";

const Layout = ({ children }: PropsWithChildren<{}>): JSX.Element => {
  console.log("--- Layout KOMPONENT STARTUJE (Wersja Przywrócona) ---");
  const currentYear = new Date().getFullYear();

  return (
    <div className={styles.appContainer}>
      <header className={styles.header}>
        <Link to="/" className={styles.logoLink}>
          European Kettlebell Championship - Live Results
        </Link>
        <nav className={styles.navigation}>
          <Link to="/" className={styles.navLink}>
            Home
          </Link>
        </nav>
      </header>

      <main className={styles.mainContent}>
        <Outlet />
      </main>

      <footer className={styles.footer}>
        <p>
          &copy; {currentYear} European Kettlebell Championship. All rights
          reserved.
        </p>
      </footer>
    </div>
  );
};

export default Layout;
