import React from "react";
import { Typography, Divider } from "antd";

const { Title, Paragraph, Link } = Typography;

const LivePage: React.FC = () => {
  // Zmienione URL - używaj formatu embed zamiast standardowego linku
  const youtubeVideoId = "ht2M89Z5Kcs";
  const youtubeEmbedUrl = `https://www.youtube.com/embed/${youtubeVideoId}`;
  const youtubeWatchUrl = `https://www.youtube.com/watch?v=${youtubeVideoId}`;

  return (
    <div>
      <Title level={1}>Transmisja Live</Title>
      <Paragraph>
        Oglądaj Mistrzostwa Europy Kettlebell na żywo! Poniżej znajdziesz linki
        do transmisji na platformie YouTube.
      </Paragraph>
      <Divider />

      <Title level={3}>Transmisja Zawodów</Title>
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
          src={youtubeEmbedUrl}
          title="Transmisja Zawodów"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        ></iframe>
      </div>
      <Paragraph>
        Link bezpośredni:{" "}
        <Link href={youtubeWatchUrl} target="_blank" rel="noopener noreferrer">
          {youtubeWatchUrl}
        </Link>
      </Paragraph>

      <Divider />
    </div>
  );
};

export default LivePage;