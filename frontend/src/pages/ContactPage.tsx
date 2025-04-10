import React from "react";
import { Typography, Card, Row, Col } from "antd";
import {
  MailOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
} from "@ant-design/icons";

const { Title, Paragraph, Link, Text } = Typography;

const ContactPage: React.FC = () => {
  return (
    <div>
      <Title level={1}>Kontakt</Title>
      <Paragraph>
        Masz pytania dotyczące zawodów, wyników lub strony? Skontaktuj się z
        nami, korzystając z poniższych informacji.
      </Paragraph>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} lg={8}>
          <Card title="Organizator Główny" bordered={false}>
            <Paragraph>
              <Text strong>Nazwa Organizacji/Stowarzyszenia</Text>
              <br />
              Ulica Przykładowa 123
              <br />
              00-001 Miasto, Kraj
              <br />
            </Paragraph>
            <Paragraph>
              <MailOutlined />{" "}
              <Link href="mailto:kontakt@example.com">kontakt@example.com</Link>
            </Paragraph>
            <Paragraph>
              <PhoneOutlined />{" "}
              <Link href="tel:+48123456789">+48 123 456 789</Link>
            </Paragraph>
          </Card>
        </Col>

        <Col xs={24} md={12} lg={8}>
          <Card title="Sprawy Techniczne (Strona WWW)" bordered={false}>
            <Paragraph>
              W przypadku problemów technicznych ze stroną wyników, prosimy o
              kontakt:
            </Paragraph>
            <Paragraph>
              <MailOutlined />{" "}
              <Link href="mailto:webmaster@example.com">
                webmaster@example.com
              </Link>
            </Paragraph>
          </Card>
        </Col>

        <Col xs={24} md={12} lg={8}>
          <Card title="Lokalizacja Zawodów" bordered={false}>
            <Paragraph>
              <EnvironmentOutlined /> Hala Sportowa "Arena Mistrzów"
              <br />
              Aleja Olimpijska 1<br />
              00-002 Miasto Sportowe
            </Paragraph>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ContactPage;
