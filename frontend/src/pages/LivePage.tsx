import React from "react";
import { Typography, Divider } from "antd";

const { Title, Paragraph, Link } = Typography;

const LivePage: React.FC = () => {
  const youtubeEmbedUrl1 = "https://www.youtube.com/embed/dQw4w9WgXcQ";
  const youtubeEmbedUrl2 = "https://www.youtube.com/embed/VIDEO_ID_2";

  return (
    <div>
      <Title level={1}>Transmisja Live</Title>
      <Paragraph>
        Oglądaj Mistrzostwa Europy Kettlebell na żywo! Poniżej znajdziesz linki
        do transmisji na platformie YouTube.
      </Paragraph>
      <Divider />

      <Title level={3}>Transmisja - Mata 1</Title>
      <div
        style={{
          position: "relative",
          paddingBottom: "56.25%",
          height: 0,
          overflow: "hidden",
          maxWidth: "100%",
          marginBottom: "1rem",
        }}
      >
        <iframe
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
          }}
          src={youtubeEmbedUrl1}
          title="Transmisja Mata 1"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        ></iframe>
      </div>
      <Paragraph>
        Link bezpośredni:{" "}
        <Link href={youtubeEmbedUrl1} target="_blank" rel="noopener noreferrer">
          {youtubeEmbedUrl1}
        </Link>
      </Paragraph>

      <Divider />

      <Title level={3}>Transmisja - Mata 2</Title>
      <div
        style={{
          position: "relative",
          paddingBottom: "56.25%",
          height: 0,
          overflow: "hidden",
          maxWidth: "100%",
          marginBottom: "1rem",
        }}
      >
        <iframe
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
          }}
          src={youtubeEmbedUrl2}
          title="Transmisja Mata 2"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        ></iframe>
      </div>
      <Paragraph>
        Link bezpośredni:{" "}
        <Link href={youtubeEmbedUrl2} target="_blank" rel="noopener noreferrer">
          {youtubeEmbedUrl2}
        </Link>
      </Paragraph>
    </div>
  );
};

export default LivePage;
