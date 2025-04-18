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


      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} lg={8}>
          <Card title="Organizator Główny" bordered={false}>
            <Paragraph>
              <Text strong>Ząbkowicka Szkoła Siły</Text>
              <br />
              Powstańców Warszawy 8i,<br />
              57-200 Ząbkowice Śląskie.
            </Paragraph>
            <Paragraph>
              <MailOutlined />{" "}
              <Link href="mailto:kontakt@example.com">ckbzabkowice@op.pl</Link>
            </Paragraph>
            <Paragraph>
              <PhoneOutlined />{" "}
              <Link href="tel:+48722166895">Błazej Sobala</Link>
            </Paragraph>
          </Card>
        </Col>

        <Col xs={24} md={12} lg={8}>
          <Card title="Facebook" bordered={false}>
            <Paragraph>
            MP Facebook
            </Paragraph>
            <Paragraph>
              <Link href="https://www.facebook.com/mphardstyle">
                MP Hardstyle Kettlebell
              </Link>
            </Paragraph>
          </Card>
        </Col>

        <Col xs={24} md={12} lg={8}>
          <Card title="Lokalizacja Zawodów" bordered={false}>
            <Paragraph>
              <EnvironmentOutlined /> Hala Sportowa "Arena Mistrzów"
              <br />
              Powstańców Warszawy 8i,<br />
              57-200 Ząbkowice Śląskie.
            </Paragraph>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ContactPage;
