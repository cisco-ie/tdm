module.exports = {
    title: 'Telemetry Data Mapper',
    description: 'Usage and Development Documentation',
    base: '/doc/',
    themeConfig: {
      sidebar: [
        '/',
        {
          title: 'Guides',
          collapsable: false,
          children: [
            '/guides/Crash Course',
            '/guides/Identifying and Validating Mappings'
          ]
        },
        {
          title: 'Developer Documentation',
          collapsable: false,
          children: [
            '/dev/architecture/Database',
            '/dev/architecture/ETL',
            '/dev/architecture/Search',
            '/dev/architecture/Web',
            '/dev/Cool Stuff'
          ]
        },
        '/Contact'
      ],
      nav: [
        { text: 'Overview', link: '/' },
        { text: 'Contact', link: '/Contact' }
      ]
    }
  }
