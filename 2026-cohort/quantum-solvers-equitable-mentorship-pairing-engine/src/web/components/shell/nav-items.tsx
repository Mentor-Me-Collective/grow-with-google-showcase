import {
  DirectoryIcon,
  HomeIcon,
  ProfileIcon,
  ResourcesIcon,
  StrandsIcon,
} from "@/components/icon/icons";

export type NavItem = {
  label: string;
  href: string;
  exact?: boolean;
  Icon: (props: { className?: string }) => React.ReactNode;
};

/** Five items, which architecture 7 sets as the ceiling for this shell. */
export function participantNav(org: string, program: string): NavItem[] {
  const base = `/o/${org}/p/${program}`;
  return [
    { label: "Home", href: base, exact: true, Icon: HomeIcon },
    { label: "Strands", href: `${base}/strands`, Icon: StrandsIcon },
    { label: "Directory", href: `${base}/directory`, Icon: DirectoryIcon },
    { label: "Resources", href: `${base}/resources`, Icon: ResourcesIcon },
    { label: "Profile", href: `${base}/me`, Icon: ProfileIcon },
  ];
}

export type NavGroup = { label: string; items: Array<Omit<NavItem, "Icon">> };

/** The six groups from architecture 7. Audit is org-scoped, reports is not. */
export function adminNav(org: string, programId: string): NavGroup[] {
  const orgBase = `/admin/o/${org}`;
  const programBase = `${orgBase}/programs/${programId}`;
  return [
    {
      label: "Overview",
      items: [{ label: "Dashboard", href: orgBase, exact: true }],
    },
    {
      label: "Setup",
      items: [
        { label: "Form", href: `${programBase}/form` },
        { label: "Criteria", href: `${programBase}/criteria` },
        { label: "Milestones", href: `${programBase}/milestones` },
        { label: "Templates", href: `${programBase}/templates` },
      ],
    },
    {
      label: "People",
      items: [
        { label: "Applications", href: `${programBase}/applications` },
        { label: "Roster", href: `${programBase}/roster` },
        { label: "Unmatched", href: `${programBase}/unmatched` },
      ],
    },
    {
      label: "Matching",
      items: [{ label: "Runs", href: `${programBase}/runs` }],
    },
    {
      label: "Running",
      items: [
        { label: "Strands", href: `${programBase}/strands` },
        { label: "Broadcast", href: `${programBase}/comms` },
      ],
    },
    {
      label: "Insight",
      items: [
        { label: "Reports", href: `${programBase}/reports` },
        { label: "Audit log", href: `${orgBase}/audit` },
      ],
    },
  ];
}
