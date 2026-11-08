// The preview resolver is only for testing a locally built SDK, not a release claim.
export default {
  webpack(config) {
    config.resolve.conditionNames = ["futureagi-gateway-preview", ...(config.resolve.conditionNames ?? ["..."])];
    config.resolve.extensionAlias = { ...config.resolve.extensionAlias, ".js": [".ts", ".tsx", ".js"] };
    return config;
  },
};
