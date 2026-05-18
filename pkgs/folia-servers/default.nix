{
  callPackage,
  lib,
  jdk21,
  jdk25,
  vanillaServers,
}:
let
  inherit (lib.our) escapeVersion;
  inherit (lib)
    nameValuePair
    flatten
    last
    versionOlder
    mapAttrsToList
    ;
  versions = lib.importJSON ./lock.json;

  # Remove -build... suffix
  stripBuild = v: builtins.head (builtins.match "(.*)-build.*" v);
  # Sort by attribute 'attr' using 'f' function
  sortBy = attr: f: builtins.sort (a: b: f a.${attr} b.${attr});

  # https://docs.papermc.io/paper/getting-started#requirements
  # Based on the paper requirements. only builds newer than 1.21 exist and are stable
  getRecommendedJavaVersion = v: if versionOlder v "26.1" then jdk21 else jdk25;

  packages = mapAttrsToList (
    mcVersion: builds:
    sortBy "version" versionOlder (
      mapAttrsToList (
        buildNumber: value:
        callPackage ./derivation.nix {
          inherit (value) url sha256;
          version = "${mcVersion}-build.${buildNumber}";
          jre = getRecommendedJavaVersion mcVersion;
          minecraft-server = vanillaServers."vanilla-${escapeVersion mcVersion}";
        }
      ) builds
    )
  ) versions;

  # Latest build for each MC version
  latestBuilds = sortBy "version" versionOlder (map last packages);
in
lib.recurseIntoAttrs (
  builtins.listToAttrs (
    (map (x: nameValuePair (escapeVersion x.name) x) (flatten packages))
    ++ (map (x: nameValuePair (escapeVersion (stripBuild x.name)) x) latestBuilds)
    ++ [ (nameValuePair "folia" (last latestBuilds)) ]
  )
)
